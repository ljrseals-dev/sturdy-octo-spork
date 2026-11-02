# Offline Rack Doc Analyzer

**v0.2 – Enhanced from original skeleton**

Offline-first pipeline for server-room / rack documentation:

```
zip → classify → local VLM (images) → local OCR (docs) → structured, typed JSON
```

Everything runs on your own hardware. No images or documents ever leave the machine.

---

## Quick start

```bash
# 1. Pull a vision model
ollama pull qwen3-vl:4b          # or gemma3:4b, llava, etc.

# 2. Environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run
python -m src.pipeline path/to/bundle.zip
# or after install: rack-analyze path/to/bundle.zip
```

Output: `output/results.json` (Pydantic-validated, human-readable).

---

## Architecture (what a future scientist should notice)

| Stage              | Responsibility                              | Why it is isolated                          |
|--------------------|---------------------------------------------|---------------------------------------------|
| `unzip_and_classify` | Physical extraction + extension routing   | Can be replaced by magic-byte / content model without touching models |
| `vlm_client`         | Local vision-language extraction          | Schema is a scientific instrument; low temperature; retries + latency |
| `ocr_client`         | Document text + layout                    | Narrow interface so Xiaomi-OCR-0 or MinerU can be swapped in |
| `schemas`            | Typed contracts (Pydantic)                | Downstream code never parses free-form JSON |
| `pipeline`           | Orchestration, progress, observability    | All side-effects live in one place          |
| `config`             | Knobs via env / .env                      | Experiments without code changes            |

### Design principles that matter

1. **Offline is a feature, not a constraint**  
   Server-room photos often contain asset tags, serial numbers, IP addresses, and physical security markers. Shipping them to a cloud VLM is both a privacy and a compliance risk. Local models turn the constraint into a product advantage.

2. **Schema-first extraction**  
   Free-form captions are almost useless for downstream automation. We force the VLM into a fixed JSON schema (`labels`, `rack_units`, `cables`, `ports`, `warnings`, `procedures`, `notes`, `confidence`). The schema itself becomes an experimental variable: change the keys, re-run, measure inter-annotator agreement against human ground truth.

3. **Observability from day one**  
   Latency per image, retry counts, and success/failure ratios are recorded. Research pipelines that skip this step become impossible to debug once the model or the prompt changes.

4. **Separation of concerns is more important than clever code**  
   Classification, vision, OCR, and orchestration are four independent modules. A scientist can improve the VLM prompt or swap the OCR backend without reading the rest of the codebase.

5. **Never commit weights or media**  
   `.gitignore` already excludes `data/`, `output/`, `*.zip`. Model weights live in Ollama or a local HF cache. This keeps the repository small and legally clean.

---

## Configuration

All important knobs live in `src/config.py` and can be overridden by environment variables:

| Variable          | Default                     | Meaning                          |
|-------------------|-----------------------------|----------------------------------|
| `OLLAMA_URL`      | `http://localhost:11434/...`| Ollama endpoint                  |
| `VLM_MODEL`       | `qwen3-vl:4b`               | Any vision model Ollama supports |
| `VLM_TIMEOUT`     | `300`                       | Seconds per image                |
| `VLM_MAX_RETRIES` | `2`                         | Automatic retries on failure     |
| `RACK_DATA_DIR`   | `./data`                    | Extraction root                  |
| `RACK_OUTPUT_DIR` | `./output`                  | Results root                     |

---

## Roadmap (research directions)

- [ ] Wire Xiaomi-OCR-0 or MinerU 2.5-Pro (layout-aware PDF)
- [ ] Batch mode with concurrent VLM calls (careful with VRAM)
- [ ] Human-in-the-loop review UI (local Gradio / Streamlit)
- [ ] Confidence calibration against a small labelled rack-photo set
- [ ] Multi-image context (same rack from different angles)
- [ ] Export to CMDB / NetBox / Excel for operations teams

---

## Insights for the next generation of scientists

**1. Treat the system prompt as an experimental apparatus**  
The prompt is version-controlled and produces a measurable schema. Changing a single instruction (“prefer RU numbers over free-form height descriptions”) is an experiment. Log the prompt hash with every result so you can reproduce findings years later.

**2. Local VLMs are already good enough for structured extraction**  
In 2025–2026 the 4 B–8 B class of vision models (Qwen2.5-VL, Gemma-3, etc.) can reliably read asset tags, port labels, and warning stickers when the prompt is constrained. You do not need a 70 B model for this task; you need a good schema and good lighting in the photographs.

**3. The bottleneck is almost never the model**  
It is usually:
- inconsistent camera angles,
- motion blur,
- missing ground-truth labels,
- or an underspecified schema.

Spend more time on data quality and evaluation metrics than on hunting for the newest model.

**4. Build the measurement layer before you scale**  
Latency, error rate, and inter-run variance should be first-class citizens. A pipeline that cannot tell you “image 47 failed because the model returned invalid JSON” is not science; it is folklore.

**5. Offline systems force better engineering**  
When you cannot call a frontier API you are forced to:
- design clear interfaces,
- handle retries and timeouts,
- keep memory footprints under control,
- and write code that other humans can read.

Those habits transfer to every future system you build.

---

## License

MIT – use it, improve it, publish the improvements.
