from sqlalchemy import select
from app.database import SessionLocal
from app.models import User,UserSkill,Skill
from app.exceptions import NotFoundError
from app.services.user_service import serialize, rating_stats
TEACH_POINTS=10;LEARN_POINTS=5;MUTUAL_BONUS=15;SAME_UNIVERSITY_BONUS=5;RATING_WEIGHT=2
def find_matches(uid,min_score,same_university_only,limit):
    with SessionLocal() as s:
        user=s.get(User,uid)
        if not user:raise NotFoundError(f"User {uid} not found")
        rows=s.scalars(select(UserSkill).order_by(UserSkill.id)).all()
        profiles={}
        for r in rows:profiles.setdefault(r.user_id,{"offer":set(),"want":set()})[r.kind].add(r.skill_id)
        mine=profiles.get(uid,{"offer":set(),"want":set()})
        names={x.id:x.name for x in s.scalars(select(Skill))}
        matches=[]
        for other in s.scalars(select(User).where(User.id!=uid)):
            same=other.university.lower()==user.university.lower()
            if same_university_only and not same:continue
            theirs=profiles.get(other.id,{"offer":set(),"want":set()})
            teach=mine["want"]&theirs["offer"]; learn=mine["offer"]&theirs["want"]
            if not teach and not learn:continue
            avg,_=rating_stats(other.id,s)
            mutual=bool(teach and learn)
            score=len(teach)*TEACH_POINTS+len(learn)*LEARN_POINTS+(MUTUAL_BONUS if mutual else 0)+(SAME_UNIVERSITY_BONUS if same else 0)+(avg or 0)*RATING_WEIGHT
            if score>=min_score:matches.append({"user":serialize(other,s),"score":round(score,2),"mutual":mutual,"can_teach_you":sorted(names[i] for i in teach),"wants_to_learn_from_you":sorted(names[i] for i in learn)})
        matches.sort(key=lambda m:(-m["score"],m["user"]["id"]))
        return matches[:limit]
