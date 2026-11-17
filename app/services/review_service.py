from datetime import datetime,timezone
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User,Swap,Review
from app.exceptions import BusinessRuleError,ConflictError,ForbiddenError,NotFoundError
def get_or_404(rid):
    with SessionLocal() as s:
        r=s.get(Review,rid)
        if not r:raise NotFoundError(f"Review {rid} not found")
        return {"id":r.id}
def create_review(data):
    with SessionLocal() as s:
        x=s.get(Swap,data.swap_id)
        if not x:raise NotFoundError(f"Swap {data.swap_id} not found")
        if not s.get(User,data.author_id):raise NotFoundError(f"User {data.author_id} not found")
        if data.author_id not in (x.requester_id,x.partner_id):raise ForbiddenError("Only participants of the swap can leave a review")
        if x.status!="completed":raise ConflictError("Reviews can only be left for completed swaps")
        if s.scalar(select(Review).where(Review.swap_id==data.swap_id,Review.author_id==data.author_id)):raise ConflictError("You have already reviewed this swap")
        reviewee=x.partner_id if data.author_id==x.requester_id else x.requester_id
        r=Review(swap_id=data.swap_id,author_id=data.author_id,reviewee_id=reviewee,rating=data.rating,comment=data.comment,created_at=datetime.now(timezone.utc));s.add(r);s.commit();s.refresh(r);return out(r)
def out(r):return {"id":r.id,"swap_id":r.swap_id,"author_id":r.author_id,"reviewee_id":r.reviewee_id,"rating":r.rating,"comment":r.comment,"created_at":r.created_at}
def list_reviews(user_id,swap_id,min_rating,limit,offset):
    with SessionLocal() as s:
        if user_id and not s.get(User,user_id):raise NotFoundError(f"User {user_id} not found")
        q=select(Review).order_by(Review.id)
        if user_id:q=q.where(Review.reviewee_id==user_id)
        if swap_id:q=q.where(Review.swap_id==swap_id)
        if min_rating is not None:q=q.where(Review.rating>=min_rating)
        return [out(r) for r in s.scalars(q.offset(offset).limit(limit))]
def get_review(rid):
    with SessionLocal() as s:
        r=s.get(Review,rid)
        if not r:raise NotFoundError(f"Review {rid} not found")
        return out(r)
def update_review(rid,data):
    with SessionLocal() as s:
        r=s.get(Review,rid)
        if not r:raise NotFoundError(f"Review {rid} not found")
        if data.author_id!=r.author_id:raise ForbiddenError("Only the author can edit the review")
        c={k:v for k,v in data.model_dump(exclude_unset=True,exclude={"author_id"}).items() if v is not None or k=="comment"}
        if not c:raise BusinessRuleError("No fields provided for update")
        for k,v in c.items():setattr(r,k,v)
        s.commit();s.refresh(r);return out(r)
def delete_review(rid,author_id):
    with SessionLocal() as s:
        r=s.get(Review,rid)
        if not r:raise NotFoundError(f"Review {rid} not found")
        if author_id!=r.author_id:raise ForbiddenError("Only the author can delete the review")
        s.delete(r);s.commit()
