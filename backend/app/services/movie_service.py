from sqlalchemy.orm import Session
from app.models.movie import Movie


def get_or_create_movie(db: Session, title: str, language: str | None = None) -> Movie:
    movie = db.query(Movie).filter(Movie.title.ilike(title)).first()
    if movie:
        return movie
    movie = Movie(title=title, external_id=f"mock-{title.lower().replace(' ', '-')}", language=language)
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie
