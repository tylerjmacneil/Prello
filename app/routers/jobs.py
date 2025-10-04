from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from supabase import create_client
import os

from ..auth import get_current_user  # relative import

router = APIRouter(prefix="/jobs", tags=["jobs"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# --- Request models ---

class JobCreate(BaseModel):
    client_id: str
    title: str
    description: Optional[str] = None
    price_cents: int
    bnpl_enabled: bool = False
    pass_fees: bool = False
    status: Optional[str] = "draft"  # 'draft'|'sent'|'signed'|'paid'|'cancelled'


# --- Stripe payment link endpoint ---
@router.post("/{job_id}/payment-link")
def create_payment_link(job_id: str, user=Depends(get_current_user)):
    import os, stripe

    # Fetch the job scoped to the current user
    job_resp = (
        supabase.table("jobs")
        .select("*").eq("id", job_id).eq("owner_user_id", user["id"])
        .single().execute()
    )
    if not job_resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    job = job_resp.data

    # Idempotent: return existing link if already created
    if job.get("stripe_payment_link_url"):
        return {
            "job_id": job_id,
            "payment_link_url": job["stripe_payment_link_url"],
            "payment_link_id": job.get("stripe_payment_link_id"),
            "price_id": job.get("stripe_price_id"),
            "product_id": job.get("stripe_product_id"),
            "existing": True,
        }

    # Stripe init
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Missing STRIPE_SECRET_KEY")

    # Create Product + Price
    product = stripe.Product.create(
        name=f"Job: {job.get('title','Untitled')}",
        metadata={"job_id": job_id, "owner_user_id": user["id"]},
    )
    price = stripe.Price.create(
        unit_amount=int(job["price_cents"]),
        currency="usd",
        product=product.id,
    )

    # Try BNPL; fall back to card-only if account disallows
    pm_types = ["card"]
    if job.get("bnpl_enabled"):
        pm_types += ["klarna", "afterpay_clearpay"]
    try:
        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            payment_method_types=pm_types,
            metadata={"job_id": job_id, "owner_user_id": user["id"]},
            after_completion={"type": "redirect", "redirect": {"url": "https://prello.app/thanks"}},
        )
    except Exception:
        link = stripe.PaymentLink.create(
            line_items=[{"price": price.id, "quantity": 1}],
            metadata={"job_id": job_id, "owner_user_id": user["id"]},
            after_completion={"type": "redirect", "redirect": {"url": "https://prello.app/thanks"}},
        )

    # Save details on the job
    supabase.table("jobs").update({
        "stripe_product_id": product.id,
        "stripe_price_id": price.id,
        "stripe_payment_link_id": link.id,
        "stripe_payment_link_url": link.url,
        "status": job.get("status") or "sent",
    }).eq("id", job_id).eq("owner_user_id", user["id"]).execute()

    return {
        "job_id": job_id,
        "payment_link_url": link.url,
        "payment_link_id": link.id,
        "price_id": price.id,
        "product_id": product.id,
        "existing": False,
    }
from fastapi import APIRouter, Depends, HTTPException
from supabase import create_client
import os

from ..auth import get_current_user  # relative import

router = APIRouter(prefix="/jobs", tags=["jobs"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# GET /jobs
@router.get("/")
def list_jobs(user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("owner_user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data

# POST /jobs
@router.post("/")
def create_job(job: dict, user=Depends(get_current_user)):
    # Minimal validation
    for key in ["client_id", "title", "price_cents"]:
        if key not in job:
            raise HTTPException(status_code=422, detail=f"Missing field: {key}")

    job["owner_user_id"] = user["id"]
    job.setdefault("status", "draft")          # expected enum in DB
    job.setdefault("bnpl_enabled", False)
    job.setdefault("pass_fees", False)

    resp = supabase.table("jobs").insert(job).execute()
    if not resp.data:
        raise HTTPException(status_code=400, detail="Failed to create job")
    return resp.data[0]

# GET /jobs/{job_id}
@router.get("/{job_id}")
def get_job(job_id: str, user=Depends(get_current_user)):
    resp = (
        supabase.table("jobs")
        .select("*")
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return resp.data[0]

# PATCH /jobs/{job_id}
@router.patch("/{job_id}")
def update_job(job_id: str, update: dict, user=Depends(get_current_user)):
    # keep ownership enforced
    resp = (
        supabase.table("jobs")
        .update(update)
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Job not found or no changes")
    return resp.data[0]

# DELETE /jobs/{job_id}
@router.delete("/{job_id}")
def delete_job(job_id: str, user=Depends(get_current_user)):
    (
        supabase.table("jobs")
        .delete()
        .eq("id", job_id)
        .eq("owner_user_id", user["id"])
        .execute()
    )
    return {"ok": True}
