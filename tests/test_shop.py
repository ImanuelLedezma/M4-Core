from commands.economy.shop import load_shop, SHOP_ITEMS

def test_shop_has_default_items():
    items = load_shop()
    assert len(items) > 0
    assert "vip" in items

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
    assert items["vip"]["name"] == "VIP"
    assert items["vip"]["price"] == 50000
    assert items["nitro"]["name"] == "Nitro Booster"
    assert items["custom_color"]["name"] == "Custom Color"
