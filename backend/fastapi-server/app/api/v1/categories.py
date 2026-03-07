from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from ...database import get_session
from ...models.algorithm import Algorithm

router = APIRouter()

CATEGORY_NAMES = {
    "supervised": "Supervised Learning",
    "unsupervised": "Unsupervised Learning",
    "probabilistic": "Probabilistic & Bayesian",
    "time-series": "Time Series & Forecasting",
    "deep-learning": "Deep Learning",
    "generative": "Generative Models",
    "graph": "Graph Machine Learning",
    "reinforcement": "Reinforcement Learning",
    "meta-learning": "Meta-Learning & AutoML",
    "evolutionary": "Evolutionary & Fuzzy Methods",
}


@router.get("/")
async def list_categories(session: Session = Depends(get_session)):
    results = session.exec(
        select(Algorithm.category, func.count(Algorithm.id)).group_by(Algorithm.category)
    ).all()
    categories = [
        {"slug": row[0], "name": CATEGORY_NAMES.get(row[0], row[0]), "count": row[1]}
        for row in results
    ]
    return {"data": categories}


@router.get("/{slug}")
async def get_category(slug: str, session: Session = Depends(get_session)):
    algorithms = session.exec(
        select(Algorithm).where(Algorithm.category == slug)
    ).all()
    if not algorithms:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Category not found")
    return {
        "data": {
            "slug": slug,
            "name": CATEGORY_NAMES.get(slug, slug),
            "algorithms": algorithms,
        }
    }
