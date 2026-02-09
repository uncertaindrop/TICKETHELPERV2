# mini_invoice_fields_pdfminer.py (fixed for multiple products)
# Outputs: name, surname, phone, invoice, "cst code", material, product, serial

import sys, re, json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine

# ---------- helpers ----------
NAME_TOKEN = r"[A-Za-zΑ-Ωα-ωΪΫϊϋΐΰάέήίόύώΆΈΉΊΌΎΏ\.-]+"
NAME_LINE_RE = re.compile(rf"^{NAME_TOKEN}(?:\s+{NAME_TOKEN})+$")
SKU_RE   = re.compile(r"^\d{6,8}$")
MONEY_RE = re.compile(r"-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})")
SERIAL_RE = re.compile(r"(\d{14,20})")
PHONE8_RE = re.compile(r"(?<!\d)([29]\d{7})(?!\d)")

# Updated invoice regex to handle both formats
INVOICE_OLD_RE = re.compile(r"Αρ\. παραστατικού:\s*([0-9]+ΑΠΔΑ[0-9]+)")
INVOICE_NEW_RE = re.compile(r"^(\d{6}ΑΠΔΑ\d{6})$")

# CST code regex
CST_RE = re.compile(r"[^\s··•]{5,}")

END_TABLE_RE = re.compile(r"(Συνολο|Σχόλια|Πληρωτέο|Καθ\.|Αξιες\s*ΦΠΑ|ΣΚΟΠΟΣ\s+ΔΙΑΚΙΝΗΣΗΣ)", re.IGNORECASE)

# Glyphs that must NEVER be considered a CST code
BAD_GLYPHS = {"·", "•", "·", "․", "‧"}

# Blacklist of terms that should never be considered names
NAME_BLACKLIST = {
    "Είδος Παραστατικού", "Παραστατικού", "Είδος",
    "ΑΠΟΔΕΙΞΗ", "ΛΙΑΝΙΚΗΣ", "Δ.ΑΠΟΣΤΟΛΗΣ",
    "Κωδικός Είδους", "Περιγραφή", "Ποσότητα",
    "Τιμή Μονάδος", "Έκπτωση", "Αξία"
}


def is_bad_cst(s: str) -> bool:
    """Reject dot-like junk sequences that pdfminer generates."""
    if not s:
        return True
    if s.strip() in BAD_GLYPHS:
        return True
    if len(s.strip()) < 5:
        return True
    # all chars are punctuation / dots?
    if all(ch in BAD_GLYPHS for ch in s.strip()):
        return True
    return False


def get_lines(pdf_path):
    lines = []
    for page in extract_pages(pdf_path):
        for el in page:
            if isinstance(el, LTTextContainer):
                for tl in el:
                    if isinstance(tl, LTTextLine):
                        s = tl.get_text().strip()
                        if s:
                            lines.append(s)
    return lines


def parse_money(s: str):
    s = s.strip().replace(" ", "")
    if "," in s and "." in s:
        if s.find(".") < s.find(","): s = s.replace(".", "")
        else: s = s.replace(",", "")
    s = s.replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d{2})", s)
    return float(m.group(0)) if m else None


def looks_like_name(s: str) -> bool:
    """Check if a string looks like a person's name"""
    if ":" in s or "Στοιχεία" in s: 
        return False
    if any(ch.isdigit() for ch in s): 
        return False
    # Check blacklist
    if s in NAME_BLACKLIST:
        return False
    if any(blacklisted in s for blacklisted in NAME_BLACKLIST):
        return False
    # Should match name pattern and be reasonable length
    if not NAME_LINE_RE.match(s):
        return False
    if len(s) > 60:
        return False
    # Should have at least 2 words for a full name
    parts = s.split()
    if len(parts) < 2:
        return False
    return True


def parse_items(lines, phone_to_exclude=""):
    """Parse items from invoice - handles both single and multiple products"""
    items = []
    
    # Find where "Κωδικός Είδους" appears (table header)
    table_start = None
    for i, line in enumerate(lines):
        if "Κωδικός Είδους" in line:
            table_start = i
            break
    
    if table_start is None:
        return items
    
    # Collect all SKUs and check if they're on the same line as descriptions
    skus = []
    sku_positions = {}
    sku_with_desc = {}  # Store descriptions that appear on same line as SKU
    
    for i in range(table_start + 1, len(lines)):
        line = lines[i].strip()
        
        # Check for standalone SKU
        if SKU_RE.match(line) and line != phone_to_exclude:
            skus.append(line)
            sku_positions[line] = i
        else:
            # Check for "SKU Description" format (e.g., "1967787 HANDSFREE APPLE...")
            parts = line.split(None, 1)  # Split on first whitespace
            if len(parts) >= 2 and SKU_RE.match(parts[0]) and parts[0] != phone_to_exclude:
                sku = parts[0]
                desc = parts[1]
                skus.append(sku)
                sku_positions[sku] = i
                # Store the description that was on the same line
                if any(keyword in desc.upper() for keyword in ["APPLE", "IPHONE", "CHARGER", "CABLE", "CASE", "USB", "SAMSUNG", "MAC", "JBL", "SPEAKER"]):
                    sku_with_desc[sku] = desc
    
    if not skus:
        return items
    
    # Find product descriptions for SKUs that don't have them yet
    max_sku_pos = max(sku_positions.values()) if sku_positions else table_start
    standalone_descriptions = []  # Descriptions that appear in the table area
    product_descriptions = {}  # Initialize the dictionary
    
    # First, use descriptions that were on the same line as SKUs
    for sku in skus:
        if sku in sku_with_desc:
            product_descriptions[sku] = sku_with_desc[sku]
    
    # Collect ALL standalone description lines in the table area (not just after last SKU)
    # Descriptions can appear between SKUs or after the last one
    for i in range(table_start + 1, min(max_sku_pos + 15, len(lines))):
        candidate = lines[i].strip()
        
        # Stop at end-of-table markers
        if any(marker in candidate for marker in ["ΣΚΟΠΟΣ ΔΙΑΚΙΝΗΣΗΣ", "ΤΟΠΟΣ ΑΠΟΣΤΟΛΗΣ", "ΣΧΟΛΙΑ", "Συνολική", "ΤΗΛΕΦΩΝΟ:", "ΠΟΛΗ:"]):
            break
        
        # Skip if it's a SKU line (standalone or at start of line)
        if SKU_RE.match(candidate):
            continue
        parts = candidate.split()
        if parts and SKU_RE.match(parts[0]) and parts[0] in [str(s) for s in skus]:
            continue
        
        # Skip table headers, labels, and serials
        if candidate in ["Ώρα", "Μ.Μ.", "Περιγραφή", "Ποσότητα", "Τιμή Μονάδος", "Σειρά", "TMX"]:
            continue
        if "Σειριακός" in candidate or "σειριακός" in candidate.lower():
            continue
        
        # Skip pure numbers and money amounts
        if candidate.replace(".", "").replace(",", "").replace(" ", "").isdigit():
            continue
        if MONEY_RE.fullmatch(candidate):
            continue
        
        # If it contains letters and looks like a product description
        if re.search(r"[A-Za-zΑ-Ωα-ω]", candidate) and len(candidate) > 3:
            # Common product keywords
            if any(keyword in candidate.upper() for keyword in ["APPLE", "IPHONE", "CHARGER", "CABLE", "CASE", "USB", "SAMSUNG", "MAC", "JBL", "SPEAKER", "EARPODS", "HANDSFREE", "PORTABLE"]):
                standalone_descriptions.append((i, candidate))  # Store with line number
    
    # Match standalone descriptions to SKUs by proximity
    # For each SKU without a description, find the nearest description line
    skus_without_desc = [sku for sku in skus if sku not in product_descriptions]
    for sku in skus_without_desc:
        sku_line = sku_positions[sku]
        # Find closest description (prefer one right after, but also check before)
        best_desc = None
        min_distance = float('inf')
        for desc_line, desc_text in standalone_descriptions:
            distance = abs(desc_line - sku_line)
            if distance < min_distance and desc_text not in product_descriptions.values():
                min_distance = distance
                best_desc = desc_text
        if best_desc:
            product_descriptions[sku] = best_desc
    
    # Collect all prices in the entire document (PDFMiner may extract in non-sequential order)
    all_prices = []
    for i, line in enumerate(lines):
        for m in MONEY_RE.findall(line):
            t = m.replace(".", "").replace(",", ".")
            try:
                val = float(t)
                # Only consider reasonable product prices
                if 10 <= val <= 10000:  # Products typically cost between 10 and 10,000
                    all_prices.append(val)
            except:
                pass
    
    # Remove duplicates and sort descending
    all_prices = sorted(list(set(all_prices)), reverse=True)
    
    # Filter out non-product prices:
    # 1. Remove VAT amounts (typically 19% of another price)
    def is_vat(price, prices, vat_rate=0.19):
        for base in prices:
            if base != price and abs(price - base * vat_rate) < 0.5:
                return True
        return False
    
    # 2. Remove sums (totals and subtotals) - check for sums of 2 or more prices
    def is_sum(price, prices):
        from itertools import combinations
        # Check sums of 2 prices
        for i, p1 in enumerate(prices):
            for p2 in prices[i+1:]:
                if p1 != price and p2 != price and abs(price - (p1 + p2)) < 1:
                    return True
        # Check sums of 3+ prices (for multi-product subtotals)
        if len(prices) >= 4:
            for count in range(3, min(len(prices), 10)):
                for combo in combinations([p for p in prices if p != price], count):
                    if abs(price - sum(combo)) < 1:
                        return True
        return False
    
    product_prices = []
    for price in all_prices:
        if not is_vat(price, all_prices) and not is_sum(price, all_prices):
            product_prices.append(price)
    
    # If filtering removed too much, fallback to using top prices
    if len(product_prices) < len(skus):
        # Take the smallest prices (products are usually cheaper than totals)
        product_prices = sorted(all_prices)[: len(skus) * 2]  # Get more candidates
        product_prices = [p for p in product_prices if p >= 10]  # Min product price
        product_prices = sorted(product_prices, reverse=True)[:len(skus)]
    
    # Match SKUs with descriptions first
    items_with_desc = []
    for sku in skus:
        desc = product_descriptions.get(sku, "")
        items_with_desc.append({"sku": sku, "desc": desc, "gross": None})
    
    # Assign prices based on product description heuristics
    # Higher-value items are typically phones, tablets, laptops
    # Lower-value items are accessories like chargers, cables, cases
    if len(items_with_desc) == len(product_prices):
        # Sort product prices descending
        sorted_prices = sorted(product_prices, reverse=True)
        
        # Create ranking of items by likely value (based on description)
        def product_value_score(desc):
            desc_upper = desc.upper()
            # Phones and tablets are high value
            if "IPHONE" in desc_upper or "IPAD" in desc_upper or "MACBOOK" in desc_upper:
                return 1000
            if "SAMSUNG" in desc_upper and "PHONE" in desc_upper:
                return 1000
            # Speakers are medium-high value
            if "SPEAKER" in desc_upper and "PORTABLE" in desc_upper:
                return 100
            if "JBL" in desc_upper:
                return 100
            # Accessories are lower value
            if "CHARGER" in desc_upper or "CABLE" in desc_upper or "CASE" in desc_upper:
                return 10
            if "EARPODS" in desc_upper or "HANDSFREE" in desc_upper:
                return 10
            # Default middle value
            return 50
        
        # Sort items by likely value
        items_with_scores = [(item, product_value_score(item["desc"])) for item in items_with_desc]
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Assign prices to items (both sorted by value, so they match)
        for (item, score), price in zip(items_with_scores, sorted_prices):
            item["gross"] = price
    
    # Fallback: if counts don't match, assign prices in order
    else:
        for idx, item in enumerate(items_with_desc):
            item["gross"] = product_prices[idx] if idx < len(product_prices) else None
    
    return items_with_desc


# CST PATTERNS
CST_SHORT_RE = re.compile(r"^[A-Za-zΑ-Ωα-ω]{1,2}\d$")          # P2, A7, Δ5
CST_10DIGIT_RE = re.compile(r"^\d{10}$")                       # 10 digits
CST_CB_RE = re.compile(r"^C[ΒB]\d{8}$")                        # CΒ + 8 digits

DATE_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")     # reject dates


def is_valid_cst(candidate: str) -> bool:
    candidate = candidate.strip()

    # Reject obvious junk
    if not candidate or len(candidate) > 12:
        return False
    if "/" in candidate or "-" in candidate:  # dates
        return False
    if DATE_RE.fullmatch(candidate):
        return False

    # Valid formats:
    if CST_SHORT_RE.fullmatch(candidate):   # P2
        return True
    if CST_10DIGIT_RE.fullmatch(candidate): # 10 digits
        return True
    if CST_CB_RE.fullmatch(candidate):      # CΒ12345678
        return True

    return False


def extract_cst(lines, full):
    # Search line-by-line for valid CST candidates
    for ln in lines:
        parts = ln.split()
        for token in parts:
            if is_valid_cst(token):
                return token

    # fallback: full text token scan
    for token in re.split(r"\s+", full):
        if is_valid_cst(token):
            return token

    return ""


def extract_invoice(lines, full):
    """Extract invoice number - handles both old and new formats"""
    # Try old format first (with prefix text)
    m = INVOICE_OLD_RE.search(full)
    if m:
        return m.group(1)
    
    # Try new format (standalone line)
    for line in lines:
        m = INVOICE_NEW_RE.match(line.strip())
        if m:
            return m.group(1)
    
    return ""


def extract_serial(lines, full):
    """Extract serial number - handles both inline and separate line formats"""
    # Find all serial numbers in the document
    serials = []
    for line in lines:
        if "Σειριακός" in line or "σειριακός" in line.lower():
            m = SERIAL_RE.search(line.replace(" ", ""))
            if m:
                serials.append(m.group(1))
    
    # Return the first serial if found (typically associated with highest-value item)
    return serials[0] if serials else ""


def extract_name_phone_new_format(lines):
    """Extract name and phone from new format"""
    name, surname, phone = "", "", ""
    
    # Look for ΕΠΩΝΥΜΙΑ: label (customer name in new format)
    # Name can appear in 1-3 lines after ΕΠΩΝΥΜΙΑ:, either as:
    # - Multiple single-word lines (e.g., "CHATZIGIAANNIS" / "KWNSTANTINOS")
    # - One multi-word line followed by more words (e.g., "VILLA CORONEL MIGUEL" / "ALEJANDRO")
    for i, line in enumerate(lines):
        if "ΕΠΩΝΥΜΙΑ:" in line:
            # Collect potential name parts from next lines
            name_parts = []
            for j in range(i + 1, min(i + 8, len(lines))):
                candidate = lines[j].strip()
                
                # Stop at certain keywords/labels
                if any(keyword in candidate for keyword in ["ΠΟΛΗ:", "Δ.Ο.Υ:", "ΤΗΛΕΦΩΝΟ:", "ΑΠΟΔΕΙΞΗ", "Ημερομηνία", "Σειρά", "Κωδικός Είδους"]):
                    break
                
                # Skip obvious non-name lines
                if "Είδος Παραστατικού" in candidate or "Παραστατικού" in candidate:
                    continue
                if "Δ.ΑΠΟΣΤΟΛΗΣ" in candidate or "ΛΙΑΝΙΚΗΣ" in candidate:
                    continue
                
                # Check if it looks like a name part
                # Accept lines with only letters, spaces, and basic punctuation
                if candidate and re.match(r"^[A-Za-zΑ-Ωα-ωΪΫϊϋΐΰάέήίόύώΆΈΉΊΌΎΏ\.\-\s]+$", candidate):
                    # It's a name part - could be single or multiple words
                    name_parts.append(candidate)
                    # Stop after collecting 2 name segments (even if one has multiple words)
                    if len(name_parts) >= 2:
                        break
            
            # If we found name parts, assign them
            if len(name_parts) >= 2:
                # Last part is first name, rest is surname
                name = name_parts[-1]
                surname = " ".join(name_parts[:-1])
                break
            elif len(name_parts) == 1:
                # Only one segment - try to split it
                words = name_parts[0].split()
                if len(words) >= 2:
                    name = words[-1]
                    surname = " ".join(words[:-1])
                else:
                    name = name_parts[0]
                break
    
    # Look for phone - scan entire document for 8-digit phone pattern (with or without +)
    # First try the standard 8-digit Cyprus format
    for line in lines:
        m = PHONE8_RE.search(line.replace(" ", ""))
        if m:
            phone = m.group(1)
            break
    
    # If no Cyprus phone found, look for international format (starts with +)
    if not phone:
        for line in lines:
            # Match international phone: + followed by 10-15 digits
            m = re.search(r'\+(\d{10,15})', line.replace(" ", ""))
            if m:
                phone = m.group(0)  # Keep the + prefix
                break
    
    return name, surname, phone


def extract_name_phone_old_format(lines):
    """Extract name and phone from old format"""
    name, surname, phone = "", "", ""
    
    # Find "Στοιχεία Πελάτη" anchor
    anchor = next((i for i, s in enumerate(lines) if "Στοιχεία Πελάτη" in s), None)
    
    if anchor is not None:
        # Look for name line
        for i in range(anchor + 1, min(len(lines), anchor + 12)):
            if looks_like_name(lines[i]):
                name_line = lines[i]
                parts = name_line.split()
                if len(parts) >= 2:
                    surname = " ".join(parts[:-1])
                    name = parts[-1]
                elif len(parts) == 1:
                    name = parts[0]
                break
        
        # Look for phone
        for i in range(anchor, min(len(lines), anchor + 15)):
            if "Τηλέφωνο:" in lines[i]:
                m = PHONE8_RE.search(lines[i].replace(" ", ""))
                if m:
                    phone = m.group(1)
                    break
    
    return name, surname, phone


def extract(pdf_path: str):
    lines = get_lines(pdf_path)
    full = "\n".join(lines)

    # Detect format by checking for old format markers
    is_old_format = any("Στοιχεία Πελάτη" in line for line in lines)
    
    # Extract invoice number
    invoice = extract_invoice(lines, full)
    
    # Extract CST code
    cst = extract_cst(lines, full)
    
    # Extract name and phone based on format (do this FIRST to get phone)
    if is_old_format:
        name, surname, phone = extract_name_phone_old_format(lines)
    else:
        name, surname, phone = extract_name_phone_new_format(lines)
    
    # Fallback: try to find name anywhere if still empty
    if not name:
        for s in lines:
            if looks_like_name(s):
                name_line = s
                parts = name_line.split()
                if len(parts) >= 2:
                    surname = " ".join(parts[:-1])
                    name = parts[-1]
                    break
                elif len(parts) == 1:
                    name = parts[0]
                    break
    
    # Fallback: try to find phone anywhere if still empty
    if not phone:
        for line in lines:
            m = PHONE8_RE.search(line.replace(" ", ""))
            if m:
                phone = m.group(1)
                break

    # Extract items → pick highest gross price (pass phone to avoid confusion)
    items = parse_items(lines, phone_to_exclude=phone)
    material = product = ""
    if items:
        best = max(items, key=lambda x: (x["gross"] or 0))
        material, product = best["sku"], best["desc"]
    
    # Extract serial number
    serial = extract_serial(lines, full)

    return {
        "name": name,
        "surname": surname,
        "phone": phone,
        "invoice": invoice,
        "cst code": cst,
        "material": material,
        "product": product,
        "serial": serial
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mini_invoice_fields_pdfminer.py /path/to/invoice.pdf")
        sys.exit(1)
    out = extract(sys.argv[1])
    print(json.dumps(out, ensure_ascii=False, indent=2))
