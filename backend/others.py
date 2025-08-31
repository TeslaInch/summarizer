STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with from
you your we our can could should would may might about over under between among across within without into onto than
i me my mine he she him her his hers its it's them they theirs us we ours who whom which what when where how why
pdf text page pages doc docs document study course topic lecture lesson exam exam(s) note notes
""".split())

def extract_keywords(text: str, k: int = 6):
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq = Counter(tokens)
    return [w for w, _ in freq.most_common(k)]

def ensure_bucket(client: Client, bucket_name: str = "pdfs"):
    try:
        client.storage.get_bucket(bucket_name)
    except Exception:
        try:
            client.storage.create_bucket(bucket_name, public=False)
        except Exception as e:
            logger.error(f"Failed to ensure bucket '{bucket_name}': {e}")

def save_summary_row(client: Client, user_id: str, filename: str, summary: str):
    try:
        client.table("summaries").insert({
            "user_id": user_id,
            "filename": filename,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Failed to save summary row: {e}")

def upload_pdf_bytes(client: Client, user_id: str, filename: str, data: bytes, bucket_name: str = "pdfs") -> str:
    ensure_bucket(client, bucket_name)
    path = f"{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    try:
        client.storage.from_(bucket_name).upload(path=path, file=data)
    except Exception as e:
        logger.error(f"Failed to upload PDF to storage: {e}")
    return path