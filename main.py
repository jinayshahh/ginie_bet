phone_number = "['+182397123']"
non_digit_chars = "+[],"

digits_only = phone_number.translate(str.maketrans("", "", non_digit_chars))

print(digits_only)