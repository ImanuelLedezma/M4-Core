from commands.economy.shop import load_shop, SHOP_ITEMS, user_has_item

def test_shop_has_default_items():
    items = load_shop()
    assert len(items) >= 9
    for key in ("donut", "pet_rock", "lucky_socks", "fake_license", "mystery_box",
                "alarm_system", "extra_luck", "stealthy_shoes", "invisibility_potion"):
        assert key in items

def test_shop_item_structure():
    items = load_shop()
    for key, item in items.items():
        assert "name" in item
        assert "description" in item
        assert "price" in item
        assert isinstance(item["price"], int)
        assert item["price"] > 0

def test_shop_default_values():
    items = load_shop()
    assert items["donut"]["name"] == "Donut"
    assert items["donut"]["price"] == 5000
    assert items["pet_rock"]["price"] == 500
    assert items["mystery_box"]["price"] == 15000
    assert items["alarm_system"]["price"] == 25000
    assert items["extra_luck"]["price"] == 30000
    assert items["stealthy_shoes"]["price"] == 45000
    assert items["invisibility_potion"]["price"] == 60000

def test_user_has_item_empty():
    assert user_has_item(999999999, "donut") is False
