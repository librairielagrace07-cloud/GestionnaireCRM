import pytest
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

from crm import User, get_all_users


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def setup_db(monkeypatch):
    """Base de données TinyDB en mémoire, qui remplace User.DB pendant le test."""
    db = TinyDB(storage=MemoryStorage)
    monkeypatch.setattr(User, "DB", db)
    yield db
    db.close()


@pytest.fixture
def user(setup_db):
    """Utilisateur de test, enregistré dans la base en mémoire."""
    u = User(first_name="Patrick",
             last_name="Martin",
             address="1 rue du chemin, 75000 Paris",
             phone_number="0123456789")
    u.save()
    return u


# ---------------------------------------------------------------------------
# Propriétés et représentations
# ---------------------------------------------------------------------------

def test_full_name(user):
    assert user.full_name == "Patrick Martin"


def test_repr(user):
    assert repr(user) == "User(Patrick, Martin)"


def test_str(user):
    assert str(user) == "Patrick Martin\n0123456789\n1 rue du chemin, 75000 Paris"


def test_db_instance(user):
    assert isinstance(user.db_instance, dict)
    assert user.db_instance["first_name"] == "Patrick"
    assert user.db_instance["last_name"] == "Martin"


def test_db_instance_not_exists(setup_db):
    u = User("Inconnu", "Absent")
    assert u.db_instance is None


# ---------------------------------------------------------------------------
# Validations
# ---------------------------------------------------------------------------

def test_check_phone_number_valid(user):
    user._check_phone_number()  # ne doit rien lever


@pytest.mark.parametrize("phone", ["+33 (6) 12 34 56 78", "06 12 34 56 78"])
def test_check_phone_number_valid_formats(setup_db, phone):
    User("Jean", "Dupont", phone_number=phone)._check_phone_number()


@pytest.mark.parametrize("phone", ["", "123", "abcdefghij", "06-12-34-56-78"])
def test_check_phone_number_invalid(setup_db, phone):
    u = User("Jean", "Dupont", phone_number=phone)
    with pytest.raises(ValueError) as err:
        u._check_phone_number()
    assert "invalide" in str(err.value)


def test_check_names_valid(user):
    user._check_names()  # ne doit rien lever


@pytest.mark.parametrize("first, last", [("", "Martin"), ("Patrick", ""), ("", "")])
def test_check_names_empty(setup_db, first, last):
    with pytest.raises(ValueError) as err:
        User(first, last)._check_names()
    assert "ne peuvent pas être vides" in str(err.value)


@pytest.mark.parametrize("first, last", [("Patrick%", "Martin"), ("Patrick", "Mart1n"), ("P@trick", "Martin")])
def test_check_names_invalid_characters(setup_db, first, last):
    with pytest.raises(ValueError) as err:
        User(first, last)._check_names()
    assert "Nom invalide" in str(err.value)


def test_checks_valid(user):
    user._checks()


# ---------------------------------------------------------------------------
# Base de données : exists / save / delete / get_all_users
# ---------------------------------------------------------------------------

def test_exists(user):
    assert user.exists() is True


def test_not_exists(setup_db):
    assert User("Inconnu", "Absent").exists() is False


def test_save(setup_db):
    u = User("Paul", "Durand", phone_number="0612345678", address="Lyon")
    doc_id = u.save()
    assert isinstance(doc_id, int)
    assert doc_id > 0
    assert u.exists()
    assert len(setup_db) == 1


def test_save_already_exists(user):
    assert user.save() == -1


def test_save_with_validation(setup_db):
    u = User("Paul", "Durand", phone_number="0612345678")
    assert u.save(validate_data=True) > 0


def test_save_with_invalid_data(setup_db):
    u = User("Paul", "Durand", phone_number="123")
    with pytest.raises(ValueError):
        u.save(validate_data=True)
    assert not u.exists()


def test_delete(user):
    deleted = user.delete()
    assert len(deleted) == 1
    assert isinstance(deleted[0], int)
    assert not user.exists()


def test_delete_not_exists(setup_db):
    assert User("Inconnu", "Absent").delete() == []


def test_get_all_users(user):
    User("Paul", "Durand").save()
    users = get_all_users()
    assert len(users) == 2
    assert all(isinstance(u, User) for u in users)
    assert {u.full_name for u in users} == {"Patrick Martin", "Paul Durand"}


def test_get_all_users_empty(setup_db):
    assert get_all_users() == []


def test_real_db_file_not_modified(user):
    """La fixture doit bien isoler les tests de db.json."""
    assert isinstance(User.DB.storage, MemoryStorage)
