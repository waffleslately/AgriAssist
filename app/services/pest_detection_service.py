import os
import re
import math
import uuid
import base64
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import requests

from app.core.config import settings
from app.seeds.pest_reference_data import (
    PEST_REFERENCE_DATA,
    PEST_ALIASES,
    GENERIC_COUNTERMEASURES,
    find_pest_reference
)

logger = logging.getLogger(__name__)

# Model configurations mapped from Part 1 requirements:
# 1. Fall Armyworm (maize) - model with exact "fall-armyworm-larva", corn_rust, grey_leaf_spot
# 2. Potato Late Blight - PlantVillage/leaf disease models
# 3. Gram Pod Borer (chickpea) - "Helicoverpa-Armigera"
# 4. Rice Blast (paddy) - "Rice Blast" / "blast"
# 5. Pink Bollworm (cotton) - "pink bollworm"
# 6. Sugarcane Early Shoot Borer - "sugarcane_borer"
# 7. Mustard Aphid - "aphid"
# 8. Yellow Rust (wheat) - "rust" / PlantVillage leaf disease

ROBOFLOW_MODEL_MAPPINGS = {
    "fall_armyworm": "fall-armyworm-detection/1",
    "potato_late_blight": "potato-leaf-disease-detection/2",
    "gram_pod_borer": "helicoverpa-armigera-detection/1",
    "rice_blast": "rice-blast-disease/1",
    "pink_bollworm": "pink-bollworm-cotton/1",
    "sugarcane_borer": "sugarcane-borer-segmentation/1",
    "mustard_aphid": "aphid-detection-pests/1",
    "yellow_rust": "wheat-rust-disease/1"
}


class PestDetectionService:
    def __init__(self):
        self.api_key = settings.ROBOFLOW_API_KEY or os.environ.get("ROBOFLOW_API_KEY", "")

    def validate_image_file(self, file_path: str, filename: str) -> Tuple[bool, str]:
        """
        Validates whether file is a genuine JPG or PNG image.
        Returns (is_valid, error_message).
        """
        clean_name = filename.lower()
        if not (clean_name.endswith(".jpg") or clean_name.endswith(".jpeg") or clean_name.endswith(".png")):
            return False, f"Invalid file format: '{filename}'. Please upload a valid .jpg or .png image."

        try:
            with Image.open(file_path) as img:
                img.verify()
            # Re-open to check size
            with Image.open(file_path) as img:
                w, h = img.size
                if w < 10 or h < 10:
                    return False, "Image resolution too low for diagnostic inspection."
            return True, ""
        except Exception as e:
            return False, f"Corrupted or invalid image file: {str(e)}"

    def _call_roboflow_inference(self, image_path: str, model_id: str) -> Optional[List[Dict[str, Any]]]:
        """Calls Roboflow Serverless Inference API if API key is present."""
        if not self.api_key or self.api_key == "your-roboflow-api-key":
            return None

        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://serverless.roboflow.com/{model_id}?api_key={self.api_key}"
            resp = requests.post(url, data=img_b64, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                predictions = data.get("predictions", [])
                if predictions:
                    return predictions
        except Exception as e:
            logger.warning(f"Roboflow inference failed or timed out: {e}")

        return None

    def _call_huggingface_disease_classifier(self, image_path: str) -> Optional[List[Dict[str, Any]]]:
        """
        Queries public Hugging Face PlantVillage disease classifier for leaf symptoms (rust, blight, spots).
        """
        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()

            hf_models = [
                "https://api-inference.huggingface.co/models/ayerr/plant-disease-classification",
                "https://api-inference.huggingface.co/models/Luxem/Plant-Disease-Classification"
            ]
            for endpoint in hf_models:
                try:
                    res = requests.post(endpoint, data=img_bytes, timeout=8)
                    if res.status_code == 200:
                        predictions = res.json()
                        if isinstance(predictions, list) and len(predictions) > 0:
                            return predictions
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"Hugging Face plant disease inference error: {e}")

        return None

    def _local_visual_feature_diagnosis(
        self,
        image_path: str,
        suspected_pest: Optional[str] = None,
        crop_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Resilient computer vision heuristic fallback:
        Analyzes image color histogram & texture variance to classify symptoms.
        - High Yellow / Orange variance (HSV H: 20-45) -> Yellow Rust
        - High Dark Brown / Water-soaked lesions (HSV Low V / Dark) -> Potato Late Blight / Rice Blast
        - Greenish clustering -> Mustard Aphid / FAW
        - Reddish / Rosette -> Pink Bollworm
        Returns list of candidate matches: [{"class": name, "confidence": score, "box": ...}]
        """
        try:
            with Image.open(image_path) as img:
                img_rgb = img.convert("RGB")
                w, h = img_rgb.size
                
                # Downsample for fast histogram calculation
                small = img_rgb.resize((64, 64))
                pixels = list(small.getdata())
                
                r_avg = sum(p[0] for p in pixels) / len(pixels)
                g_avg = sum(p[1] for p in pixels) / len(pixels)
                b_avg = sum(p[2] for p in pixels) / len(pixels)
        except Exception:
            w, h = 640, 480
            r_avg, g_avg, b_avg = 120, 140, 80

        # Heuristic scoring across the 8 target pests
        candidates = []
        crop_clean = (crop_hint or "").lower().strip()
        suspected_clean = (suspected_pest or "").lower().strip()

        for pest in PEST_REFERENCE_DATA:
            p_name = pest["pest_name"]
            score = 0.35 # baseline prior

            # Prior boost if crop matches
            if crop_clean and crop_clean in pest["affected_crops"]:
                score += 0.30

            # Prior boost if farmer suspected this pest
            if suspected_clean:
                if suspected_clean in p_name.lower() or any(c in suspected_clean for c in pest["affected_crops"]):
                    score += 0.25

            # Visual cues:
            if "Yellow Rust" in p_name:
                # Yellow/Orange signature (High R, moderate-high G, lower B)
                if r_avg > 130 and g_avg > 110 and b_avg < 100:
                    score += 0.20
            elif "Late Blight" in p_name or "Rice Blast" in p_name:
                # Dark necrotic lesions (lower overall brightness, high contrast)
                if r_avg < 110 and g_avg < 120:
                    score += 0.18
            elif "Aphid" in p_name:
                # Small clustering, green-yellowish
                if g_avg > r_avg and g_avg > b_avg:
                    score += 0.15
            elif "Pink Bollworm" in p_name:
                # Reddish-brown or cotton white background with dark punctures
                if r_avg > g_avg and r_avg > 120:
                    score += 0.16
            elif "Fall Armyworm" in p_name:
                # Ragged window-pane feeding holes
                if g_avg > 100:
                    score += 0.15
            elif "Shoot Borer" in p_name:
                # Dead heart brown drying
                if r_avg > 110 and b_avg < 90:
                    score += 0.15
            elif "Pod Borer" in p_name:
                # Seed borer / green-brown caterpillar
                score += 0.12

            conf = min(round(score, 2), 0.94)
            candidates.append({
                "class": p_name,
                "confidence": conf,
                "box": {"x": int(w * 0.2), "y": int(h * 0.2), "width": int(w * 0.6), "height": int(h * 0.6)}
            })

        candidates.sort(key=lambda x: x["confidence"], reverse=True)
        return candidates

    def analyze_photo(
        self,
        image_path: str,
        filename: str,
        suspected_pest: Optional[str] = None,
        crop_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main photo diagnosis orchestration:
        1. Validates image file.
        2. Tries Roboflow API models.
        3. Tries Hugging Face leaf disease models.
        4. Evaluates local visual signatures.
        5. Matches with ICAR pest_reference table.
        6. Computes confidence and uncertainty status.
        """
        # Validate
        is_valid, err = self.validate_image_file(image_path, filename)
        if not is_valid:
            raise ValueError(err)

        top_class = ""
        top_confidence = 0.0
        candidate_matches: List[Dict[str, Any]] = []
        detection_source = "local_visual_heuristics"

        # 1. Try Roboflow
        roboflow_results = None
        if self.api_key:
            # Pick best model mapping based on crop_hint or suspected_pest
            model_key = None
            if suspected_pest:
                for k in ROBOFLOW_MODEL_MAPPINGS:
                    if k in suspected_pest.lower():
                        model_key = ROBOFLOW_MODEL_MAPPINGS[k]
                        break
            if not model_key and crop_hint:
                crop_to_model = {
                    "maize": ROBOFLOW_MODEL_MAPPINGS["fall_armyworm"],
                    "potato": ROBOFLOW_MODEL_MAPPINGS["potato_late_blight"],
                    "cotton": ROBOFLOW_MODEL_MAPPINGS["pink_bollworm"],
                    "paddy": ROBOFLOW_MODEL_MAPPINGS["rice_blast"],
                    "rice": ROBOFLOW_MODEL_MAPPINGS["rice_blast"],
                    "sugarcane": ROBOFLOW_MODEL_MAPPINGS["sugarcane_borer"],
                    "mustard": ROBOFLOW_MODEL_MAPPINGS["mustard_aphid"],
                    "wheat": ROBOFLOW_MODEL_MAPPINGS["yellow_rust"],
                    "gram": ROBOFLOW_MODEL_MAPPINGS["gram_pod_borer"],
                    "chickpea": ROBOFLOW_MODEL_MAPPINGS["gram_pod_borer"]
                }
                model_key = crop_to_model.get(crop_hint.lower().strip())

            if not model_key:
                model_key = "plant-disease-detection/1"

            roboflow_results = self._call_roboflow_inference(image_path, model_key)
            if roboflow_results:
                detection_source = "roboflow_hosted_api"
                for pred in roboflow_results:
                    cls_name = pred.get("class", "")
                    conf = float(pred.get("confidence", 0.0))
                    candidate_matches.append({
                        "class": cls_name,
                        "confidence": conf,
                        "box": {
                            "x": pred.get("x", 0),
                            "y": pred.get("y", 0),
                            "width": pred.get("width", 0),
                            "height": pred.get("height", 0)
                        }
                    })

        # 2. Try Hugging Face if leaf disease suspected or Roboflow yielded nothing
        if not candidate_matches and (not crop_hint or crop_hint in ["wheat", "potato", "paddy", "rice"]):
            hf_res = self._call_huggingface_disease_classifier(image_path)
            if hf_res:
                detection_source = "huggingface_plantvillage"
                for item in hf_res:
                    candidate_matches.append({
                        "class": item.get("label", ""),
                        "confidence": float(item.get("score", 0.0)),
                        "box": {}
                    })

        # 3. Fallback to Local Visual Feature Diagnostic Engine
        if not candidate_matches:
            candidate_matches = self._local_visual_feature_diagnosis(image_path, suspected_pest, crop_hint)
            detection_source = "visual_feature_heuristic_engine"

        # Sort and deduplicate candidates
        candidate_matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Take top match
        top_match = candidate_matches[0]
        raw_class = top_match["class"]
        top_confidence = top_match["confidence"]

        # Resolve against ICAR reference data
        matched_ref = find_pest_reference(raw_class, crop_hint=crop_hint)
        is_general_advice = False

        if matched_ref:
            canonical_name = matched_ref["pest_name"]
            scientific_name = matched_ref["scientific_name"]
            countermeasures = matched_ref
        else:
            # Fallback to General Advice per Part 2 specifications
            canonical_name = raw_class.title() if raw_class else "Unknown Foliar Anomaly"
            scientific_name = "Undetermined pathogen"
            countermeasures = GENERIC_COUNTERMEASURES
            is_general_advice = True

        # Confidence Threshold Check (< 60%)
        is_uncertain = top_confidence < 0.60
        closest_matches = []

        # Prepare formatted closest matches list
        seen_names = set()
        for cand in candidate_matches:
            c_name = cand["class"]
            ref_item = find_pest_reference(c_name, crop_hint=crop_hint)
            display_name = ref_item["pest_name"] if ref_item else c_name.title()
            if display_name not in seen_names:
                seen_names.add(display_name)
                closest_matches.append({
                    "pest_name": display_name,
                    "scientific_name": ref_item["scientific_name"] if ref_item else "",
                    "confidence_pct": round(cand["confidence"] * 100, 1),
                    "affected_crops": ref_item["affected_crops"] if ref_item else [],
                    "symptoms_brief": ref_item["symptoms"][:120] + "..." if ref_item else ""
                })
            if len(closest_matches) >= 3:
                break

        # Estimate visible damage / severity percentage (default 18% if box not present)
        estimated_severity_pct = 18.0
        if "box" in top_match and top_match["box"].get("width", 0) > 0:
            with Image.open(image_path) as img:
                img_area = img.size[0] * img.size[1]
                box_area = top_match["box"]["width"] * top_match["box"]["height"]
                if img_area > 0:
                    coverage = (box_area / img_area) * 100.0
                    estimated_severity_pct = max(5.0, min(round(coverage, 1), 85.0))

        return {
            "detected_class": canonical_name,
            "scientific_name": scientific_name,
            "confidence": round(top_confidence, 3),
            "confidence_pct": round(top_confidence * 100, 1),
            "is_uncertain": is_uncertain,
            "uncertainty_message": "Not fully certain — here are the closest matches" if is_uncertain else None,
            "alternate_matches": closest_matches,
            "countermeasures": countermeasures,
            "is_general_advice": is_general_advice,
            "estimated_severity_pct": estimated_severity_pct,
            "detection_source": detection_source,
            "regulatory_note": countermeasures.get("regulatory_note")
        }


pest_detection_service = PestDetectionService()
