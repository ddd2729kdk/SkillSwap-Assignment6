from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models import User, Review, UserSkill, Swap
from app.exceptions import BusinessRuleError, ConflictError, NotFoundError
ACTIVE=("pending","accepted")

def get_or_404(uid, s=None):
    own=s is None; s=s or SessionLocal()
    obj=s.get(User,uid)
    if own: s.close()
    if obj is None: raise NotFoundError(f"User {uid} not found")
    return obj

def rating_stats(uid,s):
    avg,total=s.execute(select(func.avg(Review.rating),func.count(Review.id)).where(Review.reviewee_id==uid)).one()
    return (round(float(avg),2) if avg is not None else None, total)

def serialize(u,s):
    avg,total=rating_stats(u.id,s)
    return dict(id=u.id,full_name=u.full_name,email=u.email,university=u.university,major=u.major,year_of_study=u.year_of_study,bio=u.bio,created_at=u.created_at,average_rating=avg,reviews_count=total)

def create_user(data):
    with SessionLocal() as s:
        email=data.email.lower()
        if s.scalar(select(User).where(func.lower(User.email)==email)): raise ConflictError(f"Email {email} is already registered")
        u=User(**data.model_dump(exclude={"email"}),email=email); s.add(u)
        try: s.commit()
        except IntegrityError: s.rollback(); raise ConflictError(f"Email {email} is already registered")
        s.refresh(u); return serialize(u,s)

def list_users(university,skill_id,search,limit,offset):
    with SessionLocal() as s:
        q=select(User).order_by(User.id)
        if university: q=q.where(func.lower(User.university).contains(university.lower()))
        if search: q=q.where((func.lower(User.full_name).contains(search.lower()))|(func.lower(User.major).contains(search.lower())))
        if skill_id is not None: q=q.join(UserSkill).where(UserSkill.skill_id==skill_id,UserSkill.kind=="offer")
        return [serialize(u,s) for u in s.scalars(q.offset(offset).limit(limit)).unique().all()]

def get_user(uid):
    with SessionLocal() as s:
        u=s.get(User,uid)
        if not u: raise NotFoundError(f"User {uid} not found")
        return serialize(u,s)

def update_user(uid,data):
    with SessionLocal() as s:
        u=s.get(User,uid)
        if not u: raise NotFoundError(f"User {uid} not found")
        changes={k:v for k,v in data.model_dump(exclude_unset=True).items() if v is not None or k=="bio"}
        if not changes: raise BusinessRuleError("No fields provided for update")
        if "email" in changes:
            changes["email"]=changes["email"].lower()
            if s.scalar(select(User).where(func.lower(User.email)==changes["email"],User.id!=uid)): raise ConflictError(f"Email {changes['email']} is already registered")
        for k,v in changes.items(): setattr(u,k,v)
        try: s.commit()
        except IntegrityError: s.rollback(); raise ConflictError("Email is already registered")
        s.refresh(u); return serialize(u,s)

def delete_user(uid):
    with SessionLocal() as s:
        u=s.get(User,uid)
        if not u: raise NotFoundError(f"User {uid} not found")
        active=s.scalar(select(Swap.id).where((Swap.requester_id==uid)|(Swap.partner_id==uid),Swap.status.in_(ACTIVE)).limit(1))
        if active: raise ConflictError("User has pending or accepted swaps and cannot be deleted")
        swaps=list(s.scalars(select(Swap).where((Swap.requester_id==uid)|(Swap.partner_id==uid))).all())
        swap_ids=[x.id for x in swaps]
        if swap_ids: s.query(Review).filter(Review.swap_id.in_(swap_ids)).delete(synchronize_session=False)
        s.query(Review).filter((Review.author_id==uid)|(Review.reviewee_id==uid)).delete(synchronize_session=False)
        for x in swaps: s.delete(x)
        s.query(UserSkill).filter(UserSkill.user_id==uid).delete(synchronize_session=False)
        s.delete(u); s.commit()
