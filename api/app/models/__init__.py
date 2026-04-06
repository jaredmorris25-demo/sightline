# Import all models so that SQLAlchemy's mapper and Alembic's autogenerate
# can discover them via Base.metadata.
from app.models.group import Group, GroupMembership  # noqa: F401
from app.models.ingest import IngestRecord  # noqa: F401
from app.models.location import Location  # noqa: F401
from app.models.media import Media  # noqa: F401
from app.models.sighting import Sighting  # noqa: F401
from app.models.species import Species  # noqa: F401
from app.models.user import User  # noqa: F401
