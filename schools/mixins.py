class SchoolScopedQuerysetMixin:
    """
    Filtra o queryset da view por owner=request.user.
    Use em DetailView/ListView/UpdateView/DeleteView de models filhos de School.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.none()
        return qs.filter(owner=self.request.user)
