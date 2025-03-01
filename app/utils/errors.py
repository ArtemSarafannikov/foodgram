from fastapi import status


class Error(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self):
        return f"[ERROR] {self.code}: {self.message}"


recipe_not_found_err = Error(status.HTTP_404_NOT_FOUND, "Recipe not found")
user_not_found_err = Error(status.HTTP_404_NOT_FOUND, "User not found")
tag_not_found_err = Error(status.HTTP_404_NOT_FOUND, "Tag not found")
permission_denied_err = Error(status.HTTP_403_FORBIDDEN, "Permission denied")
already_in_shopping_cart_err = Error(status.HTTP_400_BAD_REQUEST, f"Already have this recipe in shopping cart")
already_in_favourite_err = Error(status.HTTP_400_BAD_REQUEST, f"Already have this recipe in favourite")
havent_recipe_in_shopping_cart_err = Error(status.HTTP_400_BAD_REQUEST, f"Haven't this recipe in shopping cart")
