# Define A Set Of Class Methods

The most common way to define class methods is by defining them directly with
`self` (the class in the current context) on a method by method basis:

```ruby
class User
  def self.find_by(attrs)
    # lookup logic ...
  end
end
```

If you have a group of class methods you want to define, you can stick them all
within a `class << self` block which does similarly defines each of them as
singleton methods of that class (`User` in this case):

```ruby
class User
  class << self
    def find_by_email(email)
      # lookup logic ...
    end

    def find_by_last_name(last_name)
      # lookup logic ...
    end
  end
end
```

This opens the singleton class of `User` for modification, adding these two new
methods.

We can see those defined alongside all other direct and inherited class methods:

```ruby
> User.methods
=>
[:find_by_email,
 :find_by_last_name,
 :yaml_tag,
 :allocate,
 ...
]
```
