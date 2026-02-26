# Import necessary libraries
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User  # Import User model
from .models import Expense
from .models import UserProfile
from datetime import datetime, timedelta
from datetime import datetime
from django.utils.timezone import now
from django.db.models import Sum
from collections import defaultdict
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import csv


# Create Expense page
@login_required(login_url='/login/')
def expenses(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date_value = request.POST.get('date')

        expense_date = datetime.strptime(date_value, "%Y-%m-%d").date()

        Expense.objects.create(
            user=request.user,
            category=category,
            amount=amount,
            description=description,
            date=expense_date
        )
        return redirect('expenses')

    queryset = Expense.objects.filter(user=request.user)

    if request.GET.get('search'):
        queryset = queryset.filter(category__icontains=request.GET.get('search'))

    total_sum = sum(exp.amount for exp in queryset)

    context = {'expenses': queryset, 'total_sum': total_sum}
    return render(request, 'expenses.html', context)

# Update the Expenses data
@login_required(login_url='/login/')
def update_expense(request, id):
    expense = Expense.objects.get(id=id)

    if request.method == 'POST':
        expense.category = request.POST.get('category')
        expense.amount = request.POST.get('amount') or 0   # ensure not null
        expense.date = request.POST.get('date')
        expense.description = request.POST.get('description')
        expense.save()
        return redirect('expenses')

    return render(request, 'update_expense.html', {'expense': expense})
# Delete the Expenses data
@login_required(login_url='/login/')
def delete_expense(request, id):
    queryset = Expense.objects.get(id=id)
    queryset.delete()
    return redirect('/')

# Login page for user
def login_page(request):
    if request.method == "POST":
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_obj = User.objects.filter(username=username).first()
            if not user_obj:
                messages.error(request, "Username not found")
                return redirect('/login/')
            user_auth = authenticate(username=username, password=password)
            if user_auth:
                login(request, user_auth)
                return redirect('expenses')
            messages.error(request, "Wrong Password")
            return redirect('/login/')
        except Exception as e:
            messages.error(request, "Something went wrong")
            return redirect('/register/')
    return render(request, "login.html")

# Register page for user
def register_page(request):
    if request.method == "POST":
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            user_obj = User.objects.filter(username=username)
            if user_obj.exists():
                messages.error(request, "Username is taken")
                return redirect('/register/')
            user_obj = User.objects.create(username=username)
            user_obj.set_password(password)
            user_obj.save()
            messages.success(request, "Account created")
            return redirect('/login')
        except Exception as e:
            messages.error(request, "Something went wrong")
            return redirect('/register')
    return render(request, "register.html")

# Logout function
def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def pdf(request):
    queryset = Expense.objects.filter(user=request.user).order_by('-date')

    grouped_expenses = defaultdict(list)
    for exp in queryset:
        month_year = exp.date.strftime("%B %Y")  # e.g., "December 2025"
        grouped_expenses[month_year].append(exp)

    # Build a list of month data for the template
    month_data = []
    for month, expenses in grouped_expenses.items():
        total = sum(exp.amount for exp in expenses)
        month_data.append({
            "month": month,
            "expenses": expenses,
            "total": total
        })

    context = {
        "month_data": month_data,
        "username": request.user.username,
        "current_month_sum": sum(exp.amount for exp in queryset if exp.date.month == now().month),
        "last_month_sum": sum(exp.amount for exp in queryset if exp.date.month == (now().month - 1)),
        "total_sum": sum(exp.amount for exp in queryset),
    }
    return render(request, "pdf.html", context)

@login_required(login_url='/login/')
def settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.currency = request.POST.get("currency", profile.currency)
        profile.monthly_budget = request.POST.get("monthly_budget", profile.monthly_budget)
        profile.notifications_enabled = "notifications_enabled" in request.POST
        profile.save()
        return redirect("dashboard")  # or stay on settings page

    context = {
        "profile": profile
    }
    return render(request, "settings.html", context)


def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    today = now().date()

    # Current month expenses
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__month=today.month,
        date__year=today.year
    )
    current_month_sum = current_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # Last month expenses
    last_month = today.month - 1 if today.month > 1 else 12
    last_month_year = today.year if today.month > 1 else today.year - 1
    last_month_expenses = Expense.objects.filter(
        user=request.user,
        date__month=last_month,
        date__year=last_month_year
    )
    last_month_sum = last_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # Savings
    savings = user_profile.monthly_budget - current_month_sum

    # Chart data
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_totals = []
    for m in range(1, 13):
        total = Expense.objects.filter(user=request.user, date__month=m, date__year=today.year).aggregate(Sum('amount'))['amount__sum'] or 0
        month_totals.append(float(total))

    categories = [choice[0] for choice in Expense.CATEGORY_CHOICES]
    category_totals = []
    for cat in categories:
        total = Expense.objects.filter(user=request.user, category=cat, date__month=today.month, date__year=today.year).aggregate(Sum('amount'))['amount__sum'] or 0
        category_totals.append(float(total))

    # Recent expenses
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date')[:5]

    context = {
        "settings": user_profile,
        "current_month_sum": current_month_sum,
        "last_month_sum": last_month_sum,
        "savings": savings,
        "months": months,
        "month_totals": month_totals,
        "categories": categories,
        "category_totals": category_totals,
        "recent_expenses": recent_expenses,
    }
    return render(request, "dashboard.html", context)


from django.shortcuts import render
from django.db.models import Sum
from django.utils.timezone import now
from .models import Expense, UserProfile

def reports(request):
    user_profile = UserProfile.objects.get(user=request.user)
    today = now().date()

    # Overall total
    total_sum = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0

    # Top category (highest spend overall)
    categories = [choice[0] for choice in Expense.CATEGORY_CHOICES]
    category_totals = []
    top_category = None
    max_spend = 0
    for cat in categories:
        total = Expense.objects.filter(user=request.user, category=cat).aggregate(Sum('amount'))['amount__sum'] or 0
        category_totals.append(float(total))
        if total > max_spend:
            max_spend = total
            top_category = cat

    # Average monthly expense (based on current year)
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_totals = []
    for m in range(1, 13):
        total = Expense.objects.filter(user=request.user, date__month=m, date__year=today.year).aggregate(Sum('amount'))['amount__sum'] or 0
        month_totals.append(float(total))
    avg_monthly = sum(month_totals) / 12 if month_totals else 0

    # Month-wise data for table
    month_data = []
    for i, m in enumerate(months, start=1):
        total = month_totals[i-1]
        difference = float(user_profile.monthly_budget) - total
        month_data.append({
            "month": m,
            "total": total,
            "difference": difference,
        })

    context = {
        "settings": user_profile,
        "total_sum": total_sum,
        "top_category": top_category,
        "avg_monthly": avg_monthly,
        "months": months,
        "month_totals": month_totals,
        "categories": categories,
        "category_totals": category_totals,
        "month_data": month_data,
    }
    return render(request, "reports.html", context)


def export_pdf(request):
    user_profile = UserProfile.objects.get(user=request.user)
    today = now().date()

    # Build month_data
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_totals = []
    for m in range(1, 13):
        total = Expense.objects.filter(user=request.user, date__month=m, date__year=today.year).aggregate(Sum('amount'))['amount__sum'] or 0
        month_totals.append(float(total))

    month_data = []
    for i, m in enumerate(months, start=1):
        total = month_totals[i-1]
        difference = float(user_profile.monthly_budget) - total
        month_data.append({"month": m, "total": total, "difference": difference})

    context = {
        "settings": user_profile,
        "month_data": month_data,
        "total_sum": sum(month_totals),
    }

    template = get_template("reports_pdf.html")  # simplified PDF template
    html = template.render(context)

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response


def export_csv(request):
    user_profile = UserProfile.objects.get(user=request.user)
    today = now().date()

    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    month_totals = []
    for m in range(1, 13):
        total = Expense.objects.filter(user=request.user, date__month=m, date__year=today.year).aggregate(Sum('amount'))['amount__sum'] or 0
        month_totals.append(float(total))

    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Month", "Total", "Budget", "Difference"])
    for i, m in enumerate(months, start=1):
        total = month_totals[i-1]
        difference = float(user_profile.monthly_budget) - total
        writer.writerow([m, total, float(user_profile.monthly_budget), difference])

    return response