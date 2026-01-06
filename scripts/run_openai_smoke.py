import asyncio
import json
import uuid

from httpx import AsyncClient

from opus_blocks.tasks.documents import run_extract_facts_job
from opus_blocks.tasks.paragraphs import run_generate_job, run_verify_job

BASE_URL = "http://localhost:8000"


def _pretty(label: str, payload: object) -> None:
    print(f"{label}:")
    print(json.dumps(payload, indent=2, sort_keys=True))


async def main() -> None:
    async with AsyncClient(base_url=BASE_URL) as client:
        email = f"user-{uuid.uuid4()}@example.com"
        password = "Password123!"
        response = await client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        response.raise_for_status()
        response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        content = (
            b"%PDF-1.4\n"
            b"Study Title: Example Outcomes\n"
            b"In a 12-week study, Treatment X reduced symptom severity by 18% "
            b"compared to placebo.\n"
            b"Participants were adults aged 40-65.\n"
            b"The study was conducted in outpatient clinics in 2022.\n"
        )
        print("Uploading PDF payload.")
        response = await client.post(
            "/api/v1/documents/upload",
            files={"file": ("example.pdf", content, "application/pdf")},
            headers=headers,
        )
        response.raise_for_status()
        document = response.json()
        print(f"Document ID: {document['id']}")

        response = await client.post(
            f"/api/v1/documents/{document['id']}/extract_facts", headers=headers
        )
        response.raise_for_status()
        extract_job = response.json()
        extract_job_id = extract_job["id"]
        await run_extract_facts_job(uuid.UUID(extract_job_id), uuid.UUID(document["id"]))
        job_status = await client.get(f"/api/v1/jobs/{extract_job_id}", headers=headers)
        job_payload = job_status.json()
        print(f"Extract job status: {job_payload['status']}")
        if job_payload.get("error"):
            print(f"Extract job error: {job_payload.get('error')}")
            if job_payload.get("progress"):
                _pretty("Extract job progress", job_payload["progress"])

        response = await client.get(f"/api/v1/documents/{document['id']}/facts", headers=headers)
        response.raise_for_status()
        facts = response.json()
        if not facts:
            runs = (
                await client.get(f"/api/v1/documents/{document['id']}/runs", headers=headers)
            ).json()
            if runs:
                _pretty("Librarian outputs", runs[0]["outputs_json"])
            response = await client.post(
                "/api/v1/facts/manual",
                json={"content": "Manual fact for OpenAI smoke flow."},
                headers=headers,
            )
            response.raise_for_status()
            fact_id = response.json()["id"]
            print("No facts extracted; using manual fact for writer.")
        else:
            fact_id = facts[0]["id"]

        response = await client.post(
            "/api/v1/manuscripts", json={"title": "OpenAI Smoke"}, headers=headers
        )
        response.raise_for_status()
        manuscript = response.json()

        spec = {
            "section": "Introduction",
            "intent": "Background Context",
            "required_structure": {
                "topic_sentence": True,
                "evidence_sentences": 1,
                "conclusion_sentence": True,
            },
            "allowed_fact_ids": [fact_id],
            "style": {"tense": "present", "voice": "academic", "target_length_words": [60, 90]},
            "constraints": {"forbidden_claims": ["novelty"], "allowed_scope": "facts only"},
        }
        response = await client.post(
            "/api/v1/paragraphs",
            json={"manuscript_id": manuscript["id"], "spec": spec},
            headers=headers,
        )
        response.raise_for_status()
        paragraph = response.json()

        response = await client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/generate", headers=headers
        )
        response.raise_for_status()
        generate_job = response.json()
        await run_generate_job(uuid.UUID(generate_job["id"]), uuid.UUID(paragraph["id"]))
        generate_status = await client.get(f"/api/v1/jobs/{generate_job['id']}", headers=headers)
        generate_payload = generate_status.json()
        print(f"Generate job status: {generate_payload['status']}")
        if generate_payload.get("error"):
            print(f"Generate job error: {generate_payload.get('error')}")
            if generate_payload.get("progress"):
                _pretty("Generate job progress", generate_payload["progress"])
        writer_runs = (
            await client.get(f"/api/v1/paragraphs/{paragraph['id']}/runs", headers=headers)
        ).json()
        writer_run = next((run for run in writer_runs if run["run_type"] == "WRITER"), None)
        if writer_run and generate_payload.get("error"):
            _pretty("Writer outputs", writer_run["outputs_json"])

        response = await client.post(
            f"/api/v1/paragraphs/{paragraph['id']}/verify", headers=headers
        )
        response.raise_for_status()
        verify_job = response.json()
        await run_verify_job(uuid.UUID(verify_job["id"]), uuid.UUID(paragraph["id"]))
        verify_status = await client.get(f"/api/v1/jobs/{verify_job['id']}", headers=headers)
        verify_payload = verify_status.json()
        print(f"Verify job status: {verify_payload['status']}")
        if verify_payload.get("error"):
            print(f"Verify job error: {verify_payload.get('error')}")
            if verify_payload.get("progress"):
                _pretty("Verify job progress", verify_payload["progress"])
        verifier_runs = (
            await client.get(f"/api/v1/paragraphs/{paragraph['id']}/runs", headers=headers)
        ).json()
        verifier_run = next((run for run in verifier_runs if run["run_type"] == "VERIFIER"), None)
        if verifier_run and verify_payload.get("error"):
            _pretty("Verifier outputs", verifier_run["outputs_json"])

        runs = (
            await client.get(f"/api/v1/paragraphs/{paragraph['id']}/runs", headers=headers)
        ).json()
        sentences = (
            await client.get(f"/api/v1/sentences/paragraph/{paragraph['id']}", headers=headers)
        ).json()
        paragraph_after = (
            await client.get(f"/api/v1/paragraphs/{paragraph['id']}", headers=headers)
        ).json()

        print(f"Runs: {[run['run_type'] for run in runs]}")
        print(f"Sentence count: {len(sentences)}")
        print(f"Paragraph status: {paragraph_after['status']}")


if __name__ == "__main__":
    asyncio.run(main())
