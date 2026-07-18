"""Verify shop data integrity — all items have required fields, valid prices,
and no missing keys that would cause runtime KeyErrors."""
from commands.economy.shop import load_shop, user_has_item

REQUIRED_KEYS = {"donut", "pet_rock", "lucky_socks", "fake_license",
                 "mystery_box", "alarm_system", "extra_luck",
                 "stealthy_shoes", "invisibility_potion"}

REQUIRED_FIELDS = {"name", "description", "price", "role"}


def verify_all_default_items_present():
    items = load_shop()
    missing = REQUIRED_KEYS - set(items.keys())
    assert not missing, f"missing shop items: {missing}"


def verify_every_item_has_required_fields():
    items = load_shop()
    for key, item in items.items():
        missing = REQUIRED_FIELDS - set(item.keys())
        assert not missing, f"item '{key}' missing fields: {missing}"


def verify_prices_are_positive_integers():
    items = load_shop()
    for key, item in items.items():
        assert isinstance(item["price"], int), f"item '{key}' price not int"
        assert item["price"] > 0, f"item '{key}' price not positive"


def verify_no_empty_descriptions():
    items = load_shop()
    for key, item in items.items():
        assert item["description"] and item["description"].strip(), f"item '{key}' has empty description"


def verify_prices_are_reasonable():
    items = load_shop()
    for key, item in items.items():
        assert item["price"] <= 100000, f"item '{key}' exceeds max price"


def verify_unknown_user_has_no_items():
    assert user_has_item(999999999, "donut") is False, "unknown user should have no items"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("verify_") and callable(fn):
            fn()
            print(f"  [OK] {name.replace('verify_', '').replace('_', ' ')}")
