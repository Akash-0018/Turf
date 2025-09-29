class MatchRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    challenger = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='match_challenges'
    )
    opponent = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='match_invitations'
    )
    preferred_date = models.DateField()
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_message = models.TextField(blank=True, null=True)
    facility_preference = models.ForeignKey(
        'facilities.Facility',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_requests'
    )
    time_preference = models.ForeignKey(
        'facilities.TimeSlot',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_requests'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.challenger.name} vs {self.opponent.name} - {self.get_status_display()}"

    def accept(self):
        self.status = 'accepted'
        self.save()

    def reject(self, message=None):
        self.status = 'rejected'
        if message:
            self.response_message = message
        self.save()

    def cancel(self):
        self.status = 'cancelled'
        self.save()