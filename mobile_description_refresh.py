from marketplace_core import MarketplaceBotConfig, run_marketplace_bot


def main() -> None:
    cfg = MarketplaceBotConfig(
        enable_sort_lowest_price=True,
        enable_description_update=True,
        back_to_list_x=35,
        back_to_list_y=90,
        post_action_sleep_s=2.0,
    )
    run_marketplace_bot(cfg)


if __name__ == "__main__":
    main()
