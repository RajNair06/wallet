import os 
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from brevo import Brevo
from brevo.transactional_emails import SendTransacEmailRequestSender,SendTransacEmailRequestToItem
from config import Config
from db.models import TransactionType

redis_broker = RedisBroker(url=Config.REDIS_URL)
dramatiq.set_broker(redis_broker)
client=Brevo(api_key=Config.BREVO_API_KEY)
@dramatiq.actor(max_retries=3)
def mail_reciept(
    transaction_id: int,
    usr_mail: str,
    amount: int,
    txn_type: str,
    currency: str,
    current_balance: int,
    from_wallet_id: int | None = None,
    to_wallet_id: int | None = None,
    reciever_name:str|None=None
):
    print(f"Worker started for transaction alert")
    print("DEBUG START", flush=True)
    print(txn_type, type(txn_type), flush=True)
    print(TransactionType.WITHDRAWAL, type(TransactionType.WITHDRAWAL), flush=True)
    print("DEBUG END", flush=True)
    html_content = ""

    txn_type_normalized = (
        txn_type.value.lower()
        if isinstance(txn_type, TransactionType)
        else str(txn_type).lower()
    )

    try:
        base_container_style = """
            max-width: 600px;
            margin: 0 auto;
            font-family: Arial, sans-serif;
            background: #f9fafb;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #e5e7eb;
            color: #111827;
        """

        heading_style = """
            margin: 0 0 16px 0;
            color: #1f2937;
            font-size: 24px;
        """

        paragraph_style = """
            margin: 0 0 12px 0;
            line-height: 1.6;
            color: #374151;
        """

        list_style = """
            background: #ffffff;
            padding: 16px 20px;
            border-radius: 10px;
            border: 1px solid #e5e7eb;
            margin: 16px 0;
        """

        item_style = "margin: 8px 0;"

        highlight_box_style = """
            background: #eef2ff;
            padding: 14px 16px;
            border-radius: 10px;
            border-left: 4px solid #4f46e5;
            margin: 16px 0;
            font-weight: 600;
        """

        footer_style = """
            margin-top: 20px;
            font-size: 13px;
            color: #6b7280;
        """

        if txn_type_normalized == TransactionType.WITHDRAWAL.value:
            subject = f"Withdrawal Confirmation - Receipt #{transaction_id}"
            html_content = f"""
            <html>
                <body style="background:#f3f4f6; padding:20px;">
                    <div style="{base_container_style}">
                        <h2 style="{heading_style}">Withdrawal Successful</h2>
                        <p style="{paragraph_style}">Hello,</p>
                        <p style="{paragraph_style}">Funds have been successfully withdrawn from your wallet.</p>

                        <div style="{highlight_box_style}">
                            Amount Withdrawn: {currency} {amount}
                        </div>

                        <ul style="{list_style}">
                            <li style="{item_style}"><strong>Transaction ID:</strong> {transaction_id}</li>
                            <li style="{item_style}"><strong>Source Wallet ID:</strong> {from_wallet_id}</li>
                            <li style="{item_style}"><strong>Amount Withdrawn:</strong> {currency} {amount}</li>
                            <li style="{item_style}"><strong>Current Balance:</strong> {currency} {current_balance}</li>
                        </ul>

                        <p style="{paragraph_style}">If you did not authorize this action, please contact support immediately.</p>
                        <p style="{footer_style}">Thank you for using our service.</p>
                    </div>
                </body>
            </html>
            """

        elif txn_type == TransactionType.DEPOSIT.value:
            subject = f"Deposit Successful - Receipt #{transaction_id}"
            html_content = f"""
            <html>
                <body style="background:#f3f4f6; padding:20px;">
                    <div style="{base_container_style}">
                        <h2 style="{heading_style}">Deposit Confirmed</h2>
                        <p style="{paragraph_style}">Hello,</p>
                        <p style="{paragraph_style}">Your deposit has been safely credited to your wallet.</p>

                        <div style="{highlight_box_style}">
                            Amount Deposited: {currency} {amount}
                        </div>

                        <ul style="{list_style}">
                            <li style="{item_style}"><strong>Transaction ID:</strong> {transaction_id}</li>
                            <li style="{item_style}"><strong>Destination Wallet ID:</strong> {to_wallet_id}</li>
                            <li style="{item_style}"><strong>Amount Deposited:</strong> {currency} {amount}</li>
                            <li style="{item_style}"><strong>Current Balance:</strong> {currency} {current_balance}</li>
                        </ul>

                        <p style="{paragraph_style}">Thank you for adding funds to your account!</p>
                        <p style="{footer_style}">We appreciate your trust in our platform.</p>
                    </div>
                </body>
            </html>
            """

        elif txn_type == TransactionType.TRANSFER.value:
            subject = f"Transfer Executed - Receipt #{transaction_id}"
            html_content = f"""
            <html>
                <body style="background:#f3f4f6; padding:20px;">
                    <div style="{base_container_style}">
                        <h2 style="{heading_style}">Transfer Complete</h2>
                        <p style="{paragraph_style}">Hello,</p>
                        <p style="{paragraph_style}">Your wallet-to-wallet transfer has been processed successfully.</p>

                        <div style="{highlight_box_style}">
                            Amount Transferred: {currency} {amount}
                        </div>

                        <ul style="{list_style}">
                            <li style="{item_style}"><strong>Transaction ID:</strong> {transaction_id}</li>
                            <li style="{item_style}"><strong>Sender Wallet ID:</strong> {from_wallet_id}</li>
                            <li style="{item_style}"><strong>Recipient Wallet ID:</strong> {to_wallet_id}</li>
                            <li style="{item_style}"><strong>Recipient Name:</strong> {reciever_name}</li>
                            <li style="{item_style}"><strong>Amount Transferred:</strong> {currency} {amount}</li>
                            <li style="{item_style}"><strong>Current Balance:</strong> {currency} {current_balance}</li>
                        </ul>

                        <p style="{paragraph_style}">Thank you for using our transfer service.</p>
                        <p style="{footer_style}">This is an automated notification.</p>
                    </div>
                </body>
            </html>
            """
        else:
            subject = f"Transaction Alert #{transaction_id}"
            html_content = f"""
            <html>
                <body style="background:#f3f4f6; padding:20px;">
                    <div style="{base_container_style}">
                        <h2 style="{heading_style}">Transaction Update</h2>
                        <p style="{paragraph_style}">Hello,</p>
                        <p style="{paragraph_style}">We have received an update on your transaction.</p>

                        <ul style="{list_style}">
                            <li style="{item_style}"><strong>Transaction ID:</strong> {transaction_id}</li>
                            <li style="{item_style}"><strong>Amount:</strong> {currency} {amount}</li>
                            <li style="{item_style}"><strong>Current Balance:</strong> {currency} {current_balance}</li>
                        </ul>
                    </div>
                </body>
            </html>
            """

        client.transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(
                email=Config.SENDER_MAIL,
                name=Config.SENDER_NAME
            ),
            to=[SendTransacEmailRequestToItem(email=usr_mail)],
            subject=subject,
            html_content=html_content
        )
        print("worker sent mail successfully")

    except Exception as e:
        print("Worker encountered an error: ", e)
        raise e