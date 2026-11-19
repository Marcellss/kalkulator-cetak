from decimal import Decimal, ROUND_HALF_UP

from django import template

register = template.Library()


def _format(value, decimals=None):
    number = Decimal(str(value))
    if decimals is not None:
        number = number.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
    integer, _, fraction = f"{number:f}".partition(".")
    negative = integer.startswith("-")
    if negative:
        integer = integer[1:]
    grouped = f"{int(integer or 0):,}".replace(",", ".")
    result = grouped + (f",{fraction}" if fraction.strip("0") else "")
    return f"-{result}" if negative else result


@register.filter
def rupiah(value):
    return f"Rp{_format(value, 2)}"


@register.filter
def nominal(value):
    return _format(value, 2)


@register.filter
def angka(value):
    text = _format(value, 4)
    return text.rstrip("0").rstrip(",") if "," in text else text


@register.filter
def plano(value):
    kiri, pemisah, kanan = str(value).partition("x")
    return f"{kiri} × {kanan} cm" if pemisah else str(value)
