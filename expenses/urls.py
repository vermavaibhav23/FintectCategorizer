from django.urls import path

from . import views


urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload_receipt, name="upload_receipt"),
    path("review-pending/", views.review_pending_expense, name="review_pending_expense"),
    path("discard-pending/", views.discard_pending_expense, name="discard_pending_expense"),
    path("expenses/<int:expense_id>/edit/", views.edit_expense, name="edit_expense"),
    path("expenses/<int:expense_id>/delete/", views.delete_expense, name="delete_expense"),
]
