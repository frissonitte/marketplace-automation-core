from marketplace_core import MarketplaceBotConfig, run_marketplace_bot


def main() -> None:
    cfg = MarketplaceBotConfig(
        enable_sort_lowest_price=False,
        enable_description_update=False,
        back_to_list_x=None,
        back_to_list_y=None,
    )
    run_marketplace_bot(cfg)


if __name__ == "__main__":
    main()
