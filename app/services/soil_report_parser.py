import io
import re
import os
import logging
from typing import Dict, Any, Optional
import pypdf
import pandas as pd

logger = logging.getLogger("agri_backend.soil_parser")

class SoilReportParser:
    """
    Multi-format Soil Health Card and laboratory report extraction pipeline.
    Accepts: PDF, Scanned Images (JPG/PNG), CSV/Excel, and Plain Typed Text.
    """

    @staticmethod
    def _clean_number(val: Any) -> Optional[float]:
        if val is None or pd.isna(val):
            return None
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip()
        # Find numeric pattern like 190, 190.5, etc.
        m = re.search(r"[-+]?\d*\.?\d+", val_str.replace(",", ""))
        if m:
            try:
                return float(m.group(0))
            except ValueError:
                return None
        return None

    def extract_from_text(self, text: str, source_format: str = "manual") -> Dict[str, Any]:
        """
        Regex + structural pattern extraction on raw extracted text.
        Supports standard English and Hindi laboratory soil health report vocabulary.
        """
        extracted = {
            "nitrogen_kg_ha": None,
            "phosphorus_kg_ha": None,
            "potassium_kg_ha": None,
            "ph": None,
            "organic_carbon_pct": None,
            "electrical_conductivity": None,
            "micronutrients": {
                "zinc": None,
                "iron": None,
                "boron": None,
                "manganese": None,
                "copper": None,
                "sulphur": None
            },
            "extraction_confidence": "low",
            "needs_manual_review": False,
            "source_format": source_format
        }

        if not text or not text.strip():
            extracted["needs_manual_review"] = True
            return extracted

        # Normalize spaces
        normalized = re.sub(r"[ \t]+", " ", text)
        lines = [l.strip() for l in normalized.split("\n") if l.strip()]

        # 1. NITROGEN (N)
        # Patterns: Nitrogen (N): 190, Available N: 190 kg/ha, उपलब्ध नाइट्रोजन 190, N: 190
        n_patterns = [
            r"(?:available\s+nitrogen|available\s+n|nitrogen\s*\(n\)|उपलब्ध\s*नाइट्रोजन|नाइट्रोजन|total\s*n|n\s*\(kg/ha\)|n)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"(?:nitrogen|नाइट्रोजन)[^\d\n\r]{1,25}([0-9]+(?:\.[0-9]+)?)\s*(?:kg/ha|किग्रा/हे|kgha|ppm)?"
        ]
        for pat in n_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                extracted["nitrogen_kg_ha"] = self._clean_number(m.group(1))
                break

        # 2. PHOSPHORUS (P / P2O5)
        p_patterns = [
            r"(?:available\s+phosphorus|available\s+p|phosphorus\s*\(p\)|p2o5|उपलब्ध\s*फास्फोरस|फास्फोरस|p\s*\(kg/ha\)|p)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"(?:phosphorus|फास्फोरस)[^\d\n\r]{1,25}([0-9]+(?:\.[0-9]+)?)\s*(?:kg/ha|किग्रा/हे|kgha|ppm)?"
        ]
        for pat in p_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                extracted["phosphorus_kg_ha"] = self._clean_number(m.group(1))
                break

        # 3. POTASSIUM (K / K2O)
        k_patterns = [
            r"(?:available\s+potassium|available\s+potash|potassium\s*\(k\)|k2o|उपलब्ध\s*पोटाश|पोटाश|k\s*\(kg/ha\)|potassium|k)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"(?:potassium|potash|पोटाश)[^\d\n\r]{1,25}([0-9]+(?:\.[0-9]+)?)\s*(?:kg/ha|किग्रा/हे|kgha|ppm)?"
        ]
        for pat in k_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                extracted["potassium_kg_ha"] = self._clean_number(m.group(1))
                break

        # 4. pH (Soil Reaction)
        ph_patterns = [
            r"(?:soil\s+ph|ph\s*\(1:2\)|ph\s*value|मृदा\s*पीएच|पीएच|ph)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)",
            r"(?:^|\s)ph\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)"
        ]
        for pat in ph_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                val = self._clean_number(m.group(1))
                if val and 3.0 <= val <= 11.0:
                    extracted["ph"] = val
                    break

        # 5. ORGANIC CARBON (OC %)
        oc_patterns = [
            r"(?:organic\s+carbon|oc\s*\(%\)|oc|जैविक\s*कार्बन|कार्बन)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)\s*%?",
            r"(?:organic\s+carbon|कार्बन)[^\d\n\r]{1,25}([0-9]+(?:\.[0-9]+)?)"
        ]
        for pat in oc_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                val = self._clean_number(m.group(1))
                if val and val <= 10.0:  # OC is typically 0.1% to 3.0%
                    extracted["organic_carbon_pct"] = val
                    break

        # 6. ELECTRICAL CONDUCTIVITY (EC dS/m)
        ec_patterns = [
            r"(?:electrical\s+conductivity|ec\s*\(ds/m\)|ec|ईसी)\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)"
        ]
        for pat in ec_patterns:
            m = re.search(pat, normalized, re.IGNORECASE)
            if m:
                extracted["electrical_conductivity"] = self._clean_number(m.group(1))
                break

        # 7. MICRONUTRIENTS (Zinc, Iron, Boron, etc.)
        for micro in ["zinc", "iron", "boron", "copper", "manganese", "sulphur"]:
            micro_pat = rf"(?:{micro}|{micro[:2]})\s*[:=\-–]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:ppm|mg/kg)?"
            m = re.search(micro_pat, normalized, re.IGNORECASE)
            if m:
                extracted["micronutrients"][micro] = self._clean_number(m.group(1))

        # Assess extraction confidence
        core_found = sum(1 for k in ["nitrogen_kg_ha", "phosphorus_kg_ha", "potassium_kg_ha", "ph"] if extracted[k] is not None)
        if core_found >= 4:
            extracted["extraction_confidence"] = "high"
            extracted["needs_manual_review"] = False
        elif core_found >= 2:
            extracted["extraction_confidence"] = "medium"
            extracted["needs_manual_review"] = True  # Recommend review for missing keys
        else:
            extracted["extraction_confidence"] = "low"
            extracted["needs_manual_review"] = True

        return extracted

    def parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from text-based PDF using pypdf.
        """
        extracted_text = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    extracted_text.append(t)
        except Exception as e:
            logger.warning(f"Error reading PDF with pypdf: {e}")

        full_text = "\n".join(extracted_text)
        if full_text.strip():
            return self.extract_from_text(full_text, source_format="pdf")

        # Scanned PDF with no embedded text
        return {
            "nitrogen_kg_ha": None,
            "phosphorus_kg_ha": None,
            "potassium_kg_ha": None,
            "ph": None,
            "organic_carbon_pct": None,
            "electrical_conductivity": None,
            "micronutrients": {},
            "extraction_confidence": "low",
            "needs_manual_review": True,
            "source_format": "pdf_scanned"
        }

    def parse_csv_or_excel(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract soil test tabular data from CSV or Excel file.
        Maps columns fuzzy-matching standard agricultural headers.
        """
        try:
            if filename.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(io.BytesIO(file_bytes))
            else:
                # Try UTF-8 then ISO-8859-1
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
                except Exception:
                    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin1")

            # Clean column names
            col_map = {}
            for col in df.columns:
                c_clean = re.sub(r"[^a-zA-Z0-9]", "", str(col).lower())
                if any(k in c_clean for k in ["nitrogen", "availn", "nitrogenc", "nkg"]):
                    col_map["n"] = col
                elif any(k in c_clean for k in ["phosphorus", "availp", "p2o5", "pkg"]):
                    col_map["p"] = col
                elif any(k in c_clean for k in ["potassium", "potash", "availk", "k2o", "kkg"]):
                    col_map["k"] = col
                elif "ph" in c_clean:
                    col_map["ph"] = col
                elif any(k in c_clean for k in ["organiccarbon", "oc", "carbon"]):
                    col_map["oc"] = col
                elif any(k in c_clean for k in ["electricalcond", "ec"]):
                    col_map["ec"] = col

            # Extract first valid row or average
            row = df.iloc[0] if len(df) > 0 else {}
            n_val = self._clean_number(row.get(col_map.get("n"))) if "n" in col_map else None
            p_val = self._clean_number(row.get(col_map.get("p"))) if "p" in col_map else None
            k_val = self._clean_number(row.get(col_map.get("k"))) if "k" in col_map else None
            ph_val = self._clean_number(row.get(col_map.get("ph"))) if "ph" in col_map else None
            oc_val = self._clean_number(row.get(col_map.get("oc"))) if "oc" in col_map else None
            ec_val = self._clean_number(row.get(col_map.get("ec"))) if "ec" in col_map else None

            found = sum(1 for v in [n_val, p_val, k_val, ph_val] if v is not None)

            return {
                "nitrogen_kg_ha": n_val,
                "phosphorus_kg_ha": p_val,
                "potassium_kg_ha": k_val,
                "ph": ph_val,
                "organic_carbon_pct": oc_val,
                "electrical_conductivity": ec_val,
                "micronutrients": {},
                "extraction_confidence": "high" if found >= 3 else ("medium" if found >= 1 else "low"),
                "needs_manual_review": found < 4,
                "source_format": "csv" if filename.lower().endswith(".csv") else "excel"
            }
        except Exception as e:
            logger.warning(f"Error parsing CSV/Excel: {e}")
            return {
                "nitrogen_kg_ha": None,
                "phosphorus_kg_ha": None,
                "potassium_kg_ha": None,
                "ph": None,
                "organic_carbon_pct": None,
                "electrical_conductivity": None,
                "micronutrients": {},
                "extraction_confidence": "low",
                "needs_manual_review": True,
                "source_format": "csv"
            }

    def parse_image(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text from report photograph or scanned image using pytesseract OCR.
        """
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(file_bytes))
            # Convert to grayscale for better OCR contrast
            gray = img.convert("L")
            ocr_text = pytesseract.image_to_string(gray)
            if ocr_text.strip():
                return self.extract_from_text(ocr_text, source_format="image")
        except Exception as e:
            logger.warning(f"Pytesseract OCR encountered exception: {e}")

        # Return structured partial fallback with needs_manual_review=True
        return {
            "nitrogen_kg_ha": None,
            "phosphorus_kg_ha": None,
            "potassium_kg_ha": None,
            "ph": None,
            "organic_carbon_pct": None,
            "electrical_conductivity": None,
            "micronutrients": {},
            "extraction_confidence": "low",
            "needs_manual_review": True,
            "source_format": "image"
        }

    def parse_file(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Main routing dispatcher for file extraction.
        """
        fn = filename.lower()
        if fn.endswith(".pdf"):
            return self.parse_pdf(file_bytes)
        elif fn.endswith((".csv", ".xlsx", ".xls")):
            return self.parse_csv_or_excel(file_bytes, filename)
        elif fn.endswith((".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff")):
            return self.parse_image(file_bytes)
        else:
            # Try decoding as plain text
            try:
                text = file_bytes.decode("utf-8")
                return self.extract_from_text(text, source_format="manual")
            except Exception:
                return {
                    "nitrogen_kg_ha": None,
                    "phosphorus_kg_ha": None,
                    "potassium_kg_ha": None,
                    "ph": None,
                    "organic_carbon_pct": None,
                    "electrical_conductivity": None,
                    "micronutrients": {},
                    "extraction_confidence": "low",
                    "needs_manual_review": True,
                    "source_format": "unknown"
                }

soil_report_parser = SoilReportParser()
