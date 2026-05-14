from sqlalchemy.orm import Session
from app.models.entity import Prompt
from app.schemas.schema import PromptCreate


class PromptService:
    def __init__(self, db: Session):
        self.db = db

    def list_prompts(self, skip: int = 0, limit: int = 100, keyword: str | None = None, tag: str | None = None) -> list[Prompt]:
        query = self.db.query(Prompt)
        if keyword:
            query = query.filter(Prompt.title.contains(keyword))
        if tag:
            query = query.filter(Prompt.tags.contains(tag))
        return query.offset(skip).limit(limit).all()

    def get_prompt(self, prompt_id: int) -> Prompt | None:
        return self.db.query(Prompt).filter(Prompt.id == prompt_id).first()

    def create_prompt(self, data: PromptCreate) -> Prompt:
        prompt = Prompt(**data.model_dump())
        self.db.add(prompt)
        self.db.commit()
        self.db.refresh(prompt)
        return prompt

    def delete_prompt(self, prompt_id: int) -> bool:
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            return False
        self.db.delete(prompt)
        self.db.commit()
        return True
