from metrics_layer import MetricsLayerConnection


def test_list_metrics(config):
    conn = MetricsLayerConnection(config=config)
    metrics = conn.list_metrics()
    assert len(metrics) == 15

    metrics = conn.list_metrics(explore_name="order_lines")
    assert len(metrics) == 15

    metrics = conn.list_metrics(view_name="order_lines", names_only=True)
    assert len(metrics) == 4
    assert set(metrics) == {
        "number_of_email_purchased_items",
        "total_item_revenue",
        "total_item_costs",
        "line_item_aov",
    }


def test_list_dimensions(config):
    conn = MetricsLayerConnection(config=config)
    dimensions = conn.list_dimensions(show_hidden=True)
    assert len(dimensions) == 34

    dimensions = conn.list_dimensions()
    assert len(dimensions) == 24

    dimensions = conn.list_dimensions(explore_name="order_lines", show_hidden=True)
    assert len(dimensions) == 33

    dimensions = conn.list_dimensions(explore_name="order_lines")
    assert len(dimensions) == 23

    dimensions = conn.list_dimensions(view_name="order_lines", names_only=True, show_hidden=True)
    dimensions_present = {
        "order_line_id",
        "order_id",
        "customer_id",
        "order",
        "waiting",
        "channel",
        "parent_channel",
        "product_name",
        "is_on_sale_sql",
        "is_on_sale_case",
        "order_tier",
    }
    assert len(dimensions) == 11
    assert set(dimensions) == dimensions_present
