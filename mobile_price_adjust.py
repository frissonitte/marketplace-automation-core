from marketplace_core import MarketplaceBotConfig, run_marketplace_bot


def main() -> None:
    cfg = MarketplaceBotConfig(
        enable_price_drop=True,
        enable_sort_lowest_price=False,
        enable_description_update=False,
        post_action_sleep_s=2.0,
    )

    print("Mobile price adjustment bot starting...")
    run_marketplace_bot(cfg)


if __name__ == "__main__":
    main()
