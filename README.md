# jqcash

gnucash ==> jq


# Installation

If you don't use `pipsi`, you're missing out.
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).

Simply run:

    $ pipsi install .


# Usage

To use it:

    $ jqcash --help

# Examples

Search,

    $ jqcash ./example.gnucash | jq 'select(.description | contains("FOOD"))'

Modify,

    $ jqcash ./example.gnucash \
    | jq 'select(.description | contains("Aldi")) | (.splits[] | select(.account.name | contains("Imbalance")).account.name) |= "Grocery"' \
    | jqcash -c ./example.gnucash

