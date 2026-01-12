DEFAULT_CURRENCY = "USD"

TAX_RATE = 0.21

COUPON_SAVE10 = "SAVE10"
COUPON_SAVE20 = "SAVE20"
COUPON_VIP = "VIP"

SAVE10_RATE = 0.10
SAVE20_RATE_HIGH = 0.20
SAVE20_RATE_LOW = 0.05
SAVE20_THRESHOLD = 200

VIP_DISCOUNT_HIGH = 50
VIP_DISCOUNT_LOW = 10
VIP_THRESHOLD = 100

ORDER_SUFFIX = "X"


def parse_request(request: dict):
    user_id = request.get("user_id")
    items = request.get("items")
    coupon = request.get("coupon")
    currency = request.get("currency")
    return user_id, items, coupon, currency


def process_checkout(request: dict) -> dict:
    user_id, items, coupon, currency = parse_request(request)

    validate_request(user_id, items)

    currency = normalize_currency(currency)
    subtotal = calc_subtotal(items)
    discount = calc_discount(subtotal, coupon)

    total_after_discount = clamp_non_negative(subtotal - discount)

    tax = calc_tax(total_after_discount)
    total = total_after_discount + tax

    order_id = generate_order_id(user_id, len(items))

    return build_response(
        order_id=order_id,
        user_id=user_id,
        currency=currency,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
        items_count=len(items),
    )


def validate_request(user_id, items) -> None:
    if user_id is None:
        raise ValueError("user_id is required")
    if items is None:
        raise ValueError("items is required")

    if type(items) is not list:
        raise ValueError("items must be a list")
    if len(items) == 0:
        raise ValueError("items must not be empty")

    validate_items(items)


def validate_items(items: list) -> None:
    for it in items:
        if "price" not in it or "qty" not in it:
            raise ValueError("item must have price and qty")
        if it["price"] <= 0:
            raise ValueError("price must be positive")
        if it["qty"] <= 0:
            raise ValueError("qty must be positive")


def normalize_currency(currency):
    if currency is None:
        return DEFAULT_CURRENCY
    return currency


def calc_subtotal(items: list) -> int:
    subtotal = 0
    for it in items:
        subtotal = subtotal + it["price"] * it["qty"]
    return subtotal


def calc_discount(subtotal: int, coupon) -> int:
    if coupon is None or coupon == "":
        return 0

    if coupon == COUPON_SAVE10:
        return int(subtotal * SAVE10_RATE)

    if coupon == COUPON_SAVE20:
        rate = SAVE20_RATE_HIGH if subtotal >= SAVE20_THRESHOLD else SAVE20_RATE_LOW
        return int(subtotal * rate)

    if coupon == COUPON_VIP:
        return VIP_DISCOUNT_LOW if subtotal < VIP_THRESHOLD else VIP_DISCOUNT_HIGH

    raise ValueError("unknown coupon")


def clamp_non_negative(value: int) -> int:
    if value < 0:
        return 0
    return value


def calc_tax(amount: int) -> int:
    return int(amount * TAX_RATE)


def generate_order_id(user_id, items_count: int) -> str:
    return str(user_id) + "-" + str(items_count) + "-" + ORDER_SUFFIX


def build_response(
    *,
    order_id: str,
    user_id,
    currency: str,
    subtotal: int,
    discount: int,
    tax: int,
    total: int,
    items_count: int,
) -> dict:
    return {
        "order_id": order_id,
        "user_id": user_id,
        "currency": currency,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "items_count": items_count,
    }
