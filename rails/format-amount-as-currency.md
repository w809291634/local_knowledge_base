# Format Amount As Currency

I was checking various sums of dollar amounts in a Rails console recently.
However, they are returned as `BigDecimal` and display in exponential notation.

```ruby
PaymentLink.joins(:payment).during(:last_month).sum("payments.amount")
# => 0.12345678e6
```

When it comes to dollar amounts I find that notation to be hard to parse at a
glance. With Rails' help I can quickly format them as currency with the
[`number_to_currency`](https://api.rubyonrails.org/classes/ActiveSupport/NumberHelper.html#method-i-number_to_currency)
method from `ActionView`'s `NumberHelper`.

```ruby
include ActionView::Helpers::NumberHelper
number_to_currency(PaymentLink.joins(:payment).during(:last_month).sum("payments.amount"))
# => "$123,456.78"
```

There are some options that can be passed to `number_to_currency` to further
customize it, like `precision`:

```ruby
number_to_currency(PaymentLink.joins(:payment).during(:last_month).sum("payments.amount"), precision: 0)
# => "$123,457"
```
