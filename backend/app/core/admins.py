from pathlib import Path

from pydantic import BaseModel


class AdminAccount(BaseModel):
    email: str
    password: str
    full_name: str | None = None


def _parse_admins(text: str) -> list[AdminAccount]:
    accounts: list[AdminAccount] = []
    current: dict[str, str] = {}

    def flush() -> None:
        if not current:
            return
        accounts.append(AdminAccount.model_validate(current))
        current.clear()

    in_list = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "admins:":
            in_list = True
            continue
        if not in_list:
            continue
        if line.startswith("- "):
            flush()
            line = line[2:].strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current[key.strip()] = value.strip().strip('"').strip("'")
    flush()
    return accounts


def load_admin_accounts(path: Path | None = None) -> list[AdminAccount]:
    file_path = path or Path(__file__).resolve().parents[2] / "config_admin.yaml"
    if not file_path.is_file():
        return []
    return _parse_admins(file_path.read_text(encoding="utf-8"))


def is_platform_admin(email: str, accounts: list[AdminAccount] | None = None) -> bool:
    wanted = email.strip().lower()
    return any(account.email.lower() == wanted for account in (accounts or load_admin_accounts()))
