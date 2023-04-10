import click
import json

from gnucash import Session, Account, Transaction, Split, Query, SessionOpenMode


def get_all_sub_accounts(account, names=[]):
    "Iterate over all sub accounts of a given account."

    for child in account.get_children_sorted():
        child_names = names.copy()
        child_names.append(child.GetName())
        yield child, "::".join(child_names)
        yield from get_all_sub_accounts(child, child_names)


def transaction_to_dict(transaction, entities):
    if transaction is None:
        return None
    else:
        simple_transaction = {}
        simple_transaction["guid"] = transaction.GetGUID().to_string()
        simple_transaction["num"] = transaction.GetNum()
        simple_transaction["notes"] = transaction.GetNotes()
        simple_transaction["is_closing_txn"] = transaction.GetIsClosingTxn()

        if "splits" in entities:
            simple_transaction["splits"] = []
            for split in transaction.GetSplitList():
                if type(split) != Split:
                    split = Split(instance=split)
                simple_transaction["splits"].append(split_to_dict(split, ["account"]))

        simple_transaction["count_splits"] = transaction.CountSplits()
        simple_transaction["has_reconciled_splits"] = transaction.HasReconciledSplits()
        simple_transaction["currency"] = transaction.GetCurrency().get_mnemonic()
        simple_transaction[
            "imbalance_value"
        ] = transaction.GetImbalanceValue().to_double()
        simple_transaction["is_balanced"] = transaction.IsBalanced()
        simple_transaction["date"] = transaction.GetDate().strftime("%Y-%m-%d")
        simple_transaction["date_posted"] = transaction.RetDatePosted().strftime(
            "%Y-%m-%d"
        )
        simple_transaction["date_entered"] = transaction.RetDateEntered().strftime(
            "%Y-%m-%d"
        )
        simple_transaction["date_due"] = transaction.RetDateDue().strftime("%Y-%m-%d")
        simple_transaction["void_status"] = transaction.GetVoidStatus()
        simple_transaction["void_time"] = transaction.GetVoidTime().strftime("%Y-%m-%d")

        simple_transaction["description"] = transaction.GetDescription()

        return simple_transaction


def split_to_dict(split, entities):
    if split is None:
        return None
    else:
        simple_split = {}
        simple_split["guid"] = split.GetGUID().to_string()
        if "account" in entities:
            simple_split["account"] = account_to_dict(split.GetAccount())
        if "transaction" in entities:
            simple_split["transaction"] = transaction_to_dict(split.GetParent(), [])
        if "other_split" in entities:
            simple_split["other_split"] = split_to_dict(
                split.GetOtherSplit(), ["account"]
            )
        simple_split["amount"] = split.GetAmount().to_double()
        simple_split["value"] = split.GetValue().to_double()
        simple_split["balance"] = split.GetBalance().to_double()
        simple_split["cleared_balance"] = split.GetClearedBalance().to_double()
        simple_split["reconciled_balance"] = split.GetReconciledBalance().to_double()

        return simple_split


def account_to_dict(account):
    commod_table = account.get_book().get_table()
    gbp = commod_table.lookup("CURRENCY", "GBP")

    if account is None:
        return None
    else:
        simple_account = {}
        simple_account["name"] = account.GetName()
        simple_account["type_id"] = account.GetType()
        simple_account["description"] = account.GetDescription()
        simple_account["guid"] = account.GetGUID().to_string()
        if account.GetCommodity() == None:
            simple_account["currency"] = ""
        else:
            simple_account["currency"] = account.GetCommodity().get_mnemonic()
        simple_account["subaccounts"] = []
        for n, subaccount in enumerate(account.get_children_sorted()):
            simple_account["subaccounts"].append(account_to_dict(subaccount))

        simple_account["balance"] = account.GetBalance().to_double()
        simple_account["balance_gbp"] = account.GetBalanceInCurrency(
            gbp, True
        ).to_double()
        simple_account["placeholder"] = account.GetPlaceholder()

        return simple_account


def get_all_transactions(book):
    query = Query()

    query.search_for("Trans")
    query.set_book(book)

    for transaction in query.run():
        yield transaction_to_dict(Transaction(instance=transaction), ['splits'])

    query.destroy()


@click.command()
@click.option("--change", "-c", is_flag=True, help="Change transactions in gnucash.")
@click.argument("file-path", required=True)
def main(file_path, change):
    """gnucash ==> jq"""
    if not change:
        with Session(
            f"xml://{file_path}", SessionOpenMode.SESSION_READ_ONLY
        ) as session:
            for t in get_all_transactions(session.book):
                click.echo(json.dumps(t))
