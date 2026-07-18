from commands.economy.shop import load_shop, SHOP_ITEMS, user_has_item

def test_shop_has_default_items():
    items = load_shop()
    assert len(items) > 0
    assert "extra_luck" in items
    assert "stealthy_shoes" in items
    assert "invisibility_potion" in items

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
    assert items["extra_luck"]["name"] == "Extra Luck"
    assert items["extra_luck"]["price"] == 30000
    assert items["stealthy_shoes"]["name"] == "Stealthy Shoes"
    assert items["stealthy_shoes"]["price"] == 45000
    assert items["invisibility_potion"]["name"] == "Invisibility Potion"
    assert items["invisibility_potion"]["price"] == 60000

def test_user_has_item_empty():
    assert user_has_item(999999999, "extra_luck") is False
