from datetime import datetime,timedelta,timezone
from sqlalchemy import select,or_
from app.database import SessionLocal
from app.models import User,Skill,UserSkill,Swap,Review,Review
from app.exceptions import BusinessRuleError,ConflictError,ForbiddenError,NotFoundError
ACTIVE_STATUSES=("pending","accepted")
TRANSITIONS={"pending":{"accepted","declined","cancelled"},"accepted":{"completed","cancelled"}}
def _now():return datetime.now(timezone.utc)
def _out(x):return {"id":x.id,"requester_id":x.requester_id,"partner_id":x.partner_id,"skill_id":x.skill_id,"skill_name":x.skill.name if x.skill else None,"offered_skill_id":x.offered_skill_id,"offered_skill_name":x.offered_skill.name if x.offered_skill else None,"message":x.message,"scheduled_at":x.scheduled_at,"duration_minutes":x.duration_minutes,"status":x.status,"created_at":x.created_at,"updated_at":x.updated_at}
def get_or_404(sid):
    with SessionLocal() as s:
        x=s.get(Swap,sid)
        if not x:raise NotFoundError(f"Swap {sid} not found")
        return {"id":x.id}
def _offers(s,uid,skill):return bool(s.scalar(select(UserSkill.id).where(UserSkill.user_id==uid,UserSkill.skill_id==skill,UserSkill.kind=="offer").limit(1)))
def _as_utc(t):
    return t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)
def _future(t):
    if _as_utc(t)<=_now():raise BusinessRuleError("Swap must be scheduled in the future")
def _free(s,uid,start,duration,exclude=None):
    end=start+timedelta(minutes=duration)
    for x in s.scalars(select(Swap).where(Swap.status=="accepted",or_(Swap.requester_id==uid,Swap.partner_id==uid))):
        if x.id==exclude:continue
        other_start=_as_utc(x.scheduled_at)
        other_end=other_start+timedelta(minutes=x.duration_minutes)
        start=_as_utc(start); end=_as_utc(end)
        if start<other_end and other_start<end:raise ConflictError(f"User {uid} already has an accepted swap that overlaps this time slot")
def create_swap(data):
    with SessionLocal() as s:
        for uid in (data.requester_id,data.partner_id):
            if not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        if data.requester_id==data.partner_id:raise BusinessRuleError("A user cannot create a swap with themselves")
        for sid in [data.skill_id,data.offered_skill_id]:
            if sid and not s.get(Skill,sid):raise NotFoundError(f"Skill {sid} not found")
        if not _offers(s,data.partner_id,data.skill_id):raise BusinessRuleError("The partner does not offer the requested skill")
        if data.offered_skill_id:
            if data.offered_skill_id==data.skill_id:raise BusinessRuleError("Offered skill must differ from the requested skill")
            if not _offers(s,data.requester_id,data.offered_skill_id):raise BusinessRuleError("The requester does not offer the skill proposed in exchange")
        _future(data.scheduled_at)
        duplicate=s.scalar(select(Swap).where(Swap.status.in_(ACTIVE_STATUSES),Swap.requester_id==data.requester_id,Swap.partner_id==data.partner_id,Swap.skill_id==data.skill_id))
        if duplicate:raise ConflictError("An active swap request for this skill and partner already exists")
        _free(s,data.requester_id,data.scheduled_at,data.duration_minutes);_free(s,data.partner_id,data.scheduled_at,data.duration_minutes)
        x=Swap(requester_id=data.requester_id,partner_id=data.partner_id,skill_id=data.skill_id,offered_skill_id=data.offered_skill_id,message=data.message,scheduled_at=data.scheduled_at,duration_minutes=data.duration_minutes,status="pending",created_at=_now(),updated_at=_now())
        s.add(x);s.commit();s.refresh(x);return _out(x)
def list_swaps(uid,status,role,limit,offset):
    with SessionLocal() as s:
        if role and uid is None:raise BusinessRuleError("The 'role' filter requires 'user_id'")
        if uid and not s.get(User,uid):raise NotFoundError(f"User {uid} not found")
        q=select(Swap).order_by(Swap.id)
        if uid:
            q=q.where(Swap.requester_id==uid if role=="requester" else Swap.partner_id==uid if role=="partner" else or_(Swap.requester_id==uid,Swap.partner_id==uid))
        if status:q=q.where(Swap.status==status.value)
        return [_out(x) for x in s.scalars(q.offset(offset).limit(limit))]
def get_swap(sid):
    with SessionLocal() as s:
        x=s.get(Swap,sid)
        if not x:raise NotFoundError(f"Swap {sid} not found")
        return _out(x)
def update_swap(sid,data):
    with SessionLocal() as s:
        x=s.get(Swap,sid)
        if not x:raise NotFoundError(f"Swap {sid} not found")
        if data.actor_id!=x.requester_id:raise ForbiddenError("Only the requester can modify the swap")
        if x.status!="pending":raise ConflictError("Only pending swaps can be modified")
        c={k:v for k,v in data.model_dump(exclude_unset=True,exclude={"actor_id"}).items() if v is not None or k=="message"}
        if not c:raise BusinessRuleError("No fields provided for update")
        if "scheduled_at" in c:_future(c["scheduled_at"])
        for k,v in c.items():setattr(x,k,v)
        x.updated_at=_now();s.commit();s.refresh(x);return _out(x)
def change_status(sid,data):
    with SessionLocal() as s:
        x=s.get(Swap,sid)
        if not x:raise NotFoundError(f"Swap {sid} not found")
        if data.actor_id not in (x.requester_id,x.partner_id):raise ForbiddenError("Only participants of the swap can change its status")
        target=data.status.value
        if target not in TRANSITIONS.get(x.status,set()):raise ConflictError(f"Cannot change swap status from '{x.status}' to '{target}'")
        if target in ("accepted","declined") and data.actor_id!=x.partner_id:raise ForbiddenError("Only the invited partner can accept or decline the swap")
        if target=="accepted":
            _future(x.scheduled_at);_free(s,x.requester_id,x.scheduled_at,x.duration_minutes,sid);_free(s,x.partner_id,x.scheduled_at,x.duration_minutes,sid)
        x.status=target;x.updated_at=_now();s.commit();s.refresh(x);return _out(x)
def delete_swap(sid,actor_id):
    with SessionLocal() as s:
        x=s.get(Swap,sid)
        if not x:raise NotFoundError(f"Swap {sid} not found")
        if actor_id not in (x.requester_id,x.partner_id):raise ForbiddenError("Only participants of the swap can delete it")
        if x.status in ACTIVE_STATUSES:raise ConflictError("Pending or accepted swaps must be cancelled before deletion")
        s.query(Review).filter(Review.swap_id==sid).delete(synchronize_session=False)
        s.delete(x);s.commit()
