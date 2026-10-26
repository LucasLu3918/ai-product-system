"""Audited topology templates, two-layer ComfyUI profiles, and draft/approve gating (synthetic, local only)."""
from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests" / "fixtures" / "creative_topology"))
import comfyui_topology
import creative_execution as creative
import creative_profiles
import golden_cases
from creative_errors import Blocked

GOLDEN = ROOT / "tests/fixtures/creative_topology/golden_before_refactor.json"
# Intentional, documented differences from the pre-refactor executor (see the core change proposal).
BINDING_REASON_NORMALIZED = {
    "f_cfg_profile", "f_clip_device", "f_clip_type", "f_latent_width", "f_max_length", "f_sampling_mode",
    "f_steps_profile", "f_system_prompt_empty", "f_thinking_true", "f_unet_name_mismatch",
}
TIGHTENED_TO_REJECT = {"z_bool_batch"}
MODEL_FILES = {
    "diffusion_models": ["z_image_turbo_bf16.safetensors", "z_image_turbo_fp8.safetensors"],
    "text_encoders": ["qwen_3_4b.safetensors"],
    "vae": ["ae.safetensors"],
}


def _load_templates() -> dict:
    return creative.load_comfy_topology_templates()


class TopologyTemplateValidationTest(unittest.TestCase):
    def setUp(self):
        self.document = yaml.safe_load((ROOT / "templates/creative/COMFYUI_TOPOLOGY_TEMPLATES.yaml").read_text(encoding="utf-8"))
        self.core = set(creative.COMFY_CORE_NODES)

    def _normalize(self, document):
        return comfyui_topology.normalize_templates(document, reviewed_ids=set(creative.COMFY_TOPOLOGY_TEMPLATE_IDS), core_classes=self.core)

    def _broken(self, mutate):
        document = copy.deepcopy(self.document)
        mutate(document["templates"])
        with self.assertRaises(Blocked) as raised:
            self._normalize(document)
        self.assertEqual(raised.exception.reason_code, comfyui_topology.TEMPLATE_REASON)

    def test_shipped_templates_cover_reviewed_ids_only(self):
        templates = _load_templates()
        self.assertEqual(set(templates), set(creative.COMFY_TOPOLOGY_TEMPLATE_IDS))
        self.assertEqual(templates["flux3_klein_t2i"]["runtime_schema_class"], "TextGenerate")
        self.assertIsNone(templates["z_image_split_loader"]["runtime_schema_class"])

    def test_unreviewed_or_missing_template_ids_are_rejected(self):
        self._broken(lambda templates: templates.update({"custom_topology": copy.deepcopy(templates["z_image_split_loader"])}))
        self._broken(lambda templates: templates.pop("flux3_klein_t2i"))

    def test_node_classes_must_stay_in_core_allowlist_and_exclude_input_images(self):
        self._broken(lambda templates: templates["z_image_split_loader"]["nodes"]["text"].update({"class_type": "CustomNode"}))
        self._broken(lambda templates: templates["z_image_split_loader"]["nodes"]["text"].update({"class_type": "LoadImage"}))
        self._broken(lambda templates: templates["z_image_split_loader"]["nodes"].update({"extra": {"class_type": "SaveImage", "inputs": ["images", "filename_prefix"]}}))

    def test_repeated_class_requires_selector_and_single_save_is_required(self):
        self._broken(lambda templates: templates["flux3_klein_t2i"]["nodes"]["clip_encoder"].pop("select"))
        self._broken(lambda templates: templates["flux3_klein_t2i"]["nodes"]["save"].update({"class_type": "PreviewImage"}))

    def test_links_bindings_and_components_must_reference_declared_names(self):
        self._broken(lambda templates: templates["z_image_split_loader"]["links"].update({"sampler.model": "ghost.0"}))
        self._broken(lambda templates: templates["z_image_split_loader"]["bindings"].append({"node": "unet", "field": "unet_name", "component": "vae_name_missing"}))
        self._broken(lambda templates: templates["z_image_split_loader"]["bindings"].append({"node": "sampler", "field": "steps", "profile": "sampler"}))
        self._broken(lambda templates: templates["flux3_klein_t2i"]["components"].append("unused_component"))

    def test_value_literals_are_not_coerced_from_yaml_booleans(self):
        # YAML 1.1 reads an unquoted off as False; the shipped template must keep the string "off".
        textgen = _load_templates()["flux3_klein_t2i"]
        sampling = [b for b in textgen["bindings"] if b.get("field") == "sampling_mode"]
        self.assertEqual(sampling[0]["value"], "off")

    def test_patched_template_data_fails_closed_for_profile_loads(self):
        with tempfile.TemporaryDirectory() as temp:
            broken = Path(temp) / "templates.yaml"
            broken.write_text("version: 1\ntemplates: {}\n", encoding="utf-8")
            with patch.object(creative, "COMFY_TOPOLOGY_TEMPLATES_PATH", broken):
                with self.assertRaises(Blocked) as raised:
                    creative.load_comfy_topology_templates()
                self.assertEqual(raised.exception.reason_code, comfyui_topology.TEMPLATE_REASON)
                self.assertIsNone(creative.load_comfy_topology_family(yaml.safe_load(creative.COMFY_PROFILE_REGISTRY_PATH.read_text()), "z_image_split_loader"))


class EquivalenceWithPreRefactorBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        cls.current = golden_cases.run_in_temp(creative)

    def test_registered_profiles_resolve_to_identical_workflows(self):
        for profile_id, expected in self.golden["system_profiles"].items():
            actual = self.current["system_profiles"][profile_id]["outcome"]
            with self.subTest(profile=profile_id):
                self.assertTrue(expected["outcome"]["accepted"])
                self.assertEqual(actual["accepted"], True)
                self.assertEqual(actual["provider"], expected["outcome"]["provider"])
                self.assertEqual(actual["final_prompt"], expected["outcome"]["final_prompt"])

    def test_mutations_keep_outcomes_except_documented_changes(self):
        for name, expected in self.golden["mutations"].items():
            actual = self.current["mutations"][name]["outcome"]
            with self.subTest(mutation=name):
                if name in TIGHTENED_TO_REJECT:
                    self.assertTrue(expected["outcome"]["accepted"])
                    self.assertEqual((actual["accepted"], actual["reason_code"]), (False, "comfy_model_profile_invalid"))
                elif name in BINDING_REASON_NORMALIZED:
                    self.assertEqual((actual["accepted"], actual["reason_code"]), (False, "comfy_model_profile_invalid"))
                    self.assertEqual(expected["outcome"]["reason_code"], "comfy_workflow_topology_invalid")
                else:
                    self.assertEqual(actual, expected["outcome"])


class UserLocalProfileTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.config_home = base / "config"
        self.models = base / "models"
        for subdir, names in MODEL_FILES.items():
            (self.models / subdir).mkdir(parents=True)
            for name in names:
                (self.models / subdir / name).write_bytes(b"synthetic weights placeholder")
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": str(self.config_home), "AIPS_COMFYUI_MODELS_DIR": str(self.models)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.network = patch("socket.socket", side_effect=AssertionError("draft and approve must not open network sockets"))
        self.network.start()
        self.addCleanup(self.network.stop)

    def _draft(self, model_id="z-image-variant", **kwargs):
        base, layer = creative.load_comfy_profile_with_layer("z-image-turbo")
        self.assertEqual(layer, "system")
        return creative_profiles.draft_profile(
            model_id=model_id, base_profile_id="z-image-turbo", base_profile=base, models_dir=None,
            profile_id=kwargs.pop("profile_id", None), overrides=kwargs.pop("overrides", {"unet_name": "z_image_turbo_bf16.safetensors"}),
            reserved_ids=creative.system_profile_ids(), validate=creative.validate_local_profile_body)

    def _approve(self, profile_id, *, interactive=True, phrase=None):
        expected = phrase if phrase is not None else f"APPROVE {profile_id}"
        return creative_profiles.approve_profile(profile_id, models_dir=None, validate=creative.validate_local_profile_body,
                                                 interactive=interactive, read_line=lambda _prompt: expected, summary_stream=io.StringIO())

    def _draft_path(self, profile_id):
        return self.config_home / "aips/creative/profiles" / f"{profile_id}.yaml"

    def test_draft_is_unapproved_names_only_and_offline(self):
        result = self._draft()
        self.assertEqual(result["status"], "DRAFTED")
        self.assertEqual(result["approval_status"], "UNAPPROVED")
        self.assertEqual(result["profile_id"], "local-z-image-variant")
        self.assertEqual(result["template_id"], "z_image_split_loader")
        text = json.dumps(result)
        self.assertNotIn(self.temp.name, text)
        draft = yaml.safe_load(self._draft_path("local-z-image-variant").read_text(encoding="utf-8"))
        self.assertEqual(draft["status"], "UNAPPROVED")
        self.assertNotIn(self.temp.name, self._draft_path("local-z-image-variant").read_text(encoding="utf-8"))
        self.assertFalse((self.config_home / "aips/creative/profile-approvals.json").exists())

    def test_draft_ambiguous_component_requires_explicit_selection(self):
        with self.assertRaises(Blocked) as raised:
            self._draft(overrides={})
        self.assertEqual(raised.exception.reason_code, "profile_component_ambiguous")
        self.assertFalse(self._draft_path("local-z-image-variant").exists())

    def test_draft_rejects_uninstalled_weights_reserved_ids_and_overwrites(self):
        with self.assertRaises(Blocked) as missing:
            self._draft(overrides={"unet_name": "not_installed.safetensors"})
        self.assertEqual(missing.exception.reason_code, "profile_component_not_found")
        with self.assertRaises(Blocked) as reserved:
            self._draft(profile_id="z-image-turbo")
        self.assertEqual(reserved.exception.reason_code, "profile_id_reserved")
        with self.assertRaises(Blocked) as invalid:
            self._draft(profile_id="../escape")
        self.assertEqual(invalid.exception.reason_code, "profile_id_invalid")
        self._draft()
        with self.assertRaises(Blocked) as exists:
            self._draft()
        self.assertEqual(exists.exception.reason_code, "profile_draft_exists")

    def test_approval_refuses_without_interactive_terminal_and_writes_nothing(self):
        self._draft()
        with self.assertRaises(Blocked) as raised:
            self._approve("local-z-image-variant", interactive=False)
        self.assertEqual(raised.exception.reason_code, "profile_approval_requires_tty")
        self.assertIn("UNAPPROVED", self._draft_path("local-z-image-variant").read_text(encoding="utf-8"))
        self.assertFalse((self.config_home / "aips/creative/profile-approvals.json").exists())

    def test_wrong_confirmation_phrase_is_declined_without_record(self):
        self._draft()
        with self.assertRaises(Blocked) as raised:
            self._approve("local-z-image-variant", phrase="yes")
        self.assertEqual(raised.exception.reason_code, "profile_approval_declined")
        self.assertFalse((self.config_home / "aips/creative/profile-approvals.json").exists())

    def test_approved_profile_loads_only_while_its_hash_matches(self):
        self._draft()
        result = self._approve("local-z-image-variant")
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["inference"], "NOT_RUN")
        profile, layer = creative.load_comfy_profile_with_layer("local-z-image-variant")
        self.assertEqual(layer, "user_local")
        self.assertEqual(profile["topology"], "z_image_split_loader")
        path = self._draft_path("local-z-image-variant")
        path.write_text(path.read_text(encoding="utf-8").replace("cfg: 1", "cfg: 2"), encoding="utf-8")
        with self.assertRaises(Blocked) as stale:
            creative.load_comfy_profile_with_layer("local-z-image-variant")
        self.assertEqual(stale.exception.reason_code, "profile_not_approved")

    def test_user_local_profiles_cannot_add_topology_nodes_or_endpoints(self):
        self._draft()
        path = self._draft_path("local-z-image-variant")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["nodes"] = {"99": {"class_type": "CustomNode"}}
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with self.assertRaises(Blocked) as raised:
            self._approve("local-z-image-variant")
        self.assertEqual(raised.exception.reason_code, "profile_local_restricted")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        del document["nodes"]
        document["topology"] = "custom_topology"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with self.assertRaises(Blocked) as topology:
            self._approve("local-z-image-variant")
        self.assertEqual(topology.exception.reason_code, "profile_local_restricted")

    def test_user_local_values_stay_within_family_ranges_and_file_names(self):
        self._draft()
        path = self._draft_path("local-z-image-variant")
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        document["sampler"]["cfg"] = 31
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with self.assertRaises(Blocked) as cfg:
            self._approve("local-z-image-variant")
        self.assertEqual(cfg.exception.reason_code, "comfy_model_profile_invalid")
        document["sampler"]["cfg"] = 1
        document["components"]["vae_name"] = "../ae.safetensors"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with self.assertRaises(Blocked) as traversal:
            self._approve("local-z-image-variant")
        self.assertEqual(traversal.exception.reason_code, "comfy_model_profile_invalid")

    def test_approval_requires_weights_to_be_installed_at_approval_time(self):
        self._draft()
        (self.models / "vae" / "ae.safetensors").unlink()
        with self.assertRaises(Blocked) as raised:
            self._approve("local-z-image-variant")
        self.assertEqual(raised.exception.reason_code, "profile_smoke_failed")
        self.assertEqual(raised.exception.diagnostics, {"failed_components": ["vae_name"]})

    def test_local_profile_resolves_through_the_audited_template(self):
        self._draft(model_id="z-image-variant")
        self._approve("local-z-image-variant")
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))["system_profiles"]["z-image-turbo"]
        config = {**golden["config"], "model_profile": "local-z-image-variant", "model_id": "z-image-variant"}
        workflow = golden_cases.load_source(golden_cases.ZIMAGE_SOURCE)
        root = Path(self.temp.name) / "project"
        root.mkdir()
        (root / "flow.json").write_text(json.dumps(workflow), encoding="utf-8")
        _, info = creative.load_comfy_workflow(root.resolve(), {**config, "workflow_path": "flow.json"})
        self.assertEqual(info["profile_layer"], "user_local")
        self.assertEqual(info["sampler_node_id"], "3")
        self.assertEqual(info["profile"]["model_id"], "z-image-variant")

    def test_non_tty_cli_refuses_approval_with_stable_reason(self):
        self._draft()
        env = {**os.environ, "XDG_CONFIG_HOME": str(self.config_home), "AIPS_COMFYUI_MODELS_DIR": str(self.models)}
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/creative_execution.py"), "profile", "approve", "local-z-image-variant"],
            input="APPROVE local-z-image-variant\n", capture_output=True, text=True, env=env, cwd=ROOT, check=False)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["reason_code"], "profile_approval_requires_tty")
        self.assertNotIn(self.temp.name, result.stdout + result.stderr)
        self.assertFalse((self.config_home / "aips/creative/profile-approvals.json").exists())

    def test_cli_draft_is_bounded_and_privacy_safe(self):
        env = {**os.environ, "XDG_CONFIG_HOME": str(self.config_home), "AIPS_COMFYUI_MODELS_DIR": str(self.models)}
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/creative_execution.py"), "profile", "draft", "--model-id", "z-image-variant",
             "--base-profile", "z-image-turbo", "--component", "unet_name=z_image_turbo_bf16.safetensors"],
            capture_output=True, text=True, env=env, cwd=ROOT, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["approval_status"], "UNAPPROVED")
        self.assertNotIn(self.temp.name, result.stdout)


if __name__ == "__main__":
    unittest.main()
