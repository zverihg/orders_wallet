from main.infra.models.customer_models.models import Customer


class CustomerRepo:

    def get_customer_by_id(self, customer_id: int) -> dict:

        obj = Customer.objects.get(id=customer_id)

        return obj.__dict__

    def get_or_create_customer(self, customer_id: int) -> dict:

        obj = Customer.objects.get_or_create(id=customer_id)

        return obj.__dict__

    def create_customer(self, name: str) -> dict:

        obj = Customer.objects.create(name=name)

        return obj.__dict__


customer_repo = CustomerRepo()