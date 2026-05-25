23/05/2026

created user model and auth logic with jwt 
alemic migration setup

24/05/25

create wallet and transaction model
implement route handler for creating,deleting wallet and fetching wallet details

now what i need to do is to implement transactions like depositing to a wallet , transfering from one wallet to another , withdrawing from own wallet 

25/05/26

faced an issue with alembic migration , it wasnt injecting sqlmodel with every migration script and so thats why i made modifications in the script.mako.py by adding an import statement .

and another thing sqlite cant process alter existing columns that can be achieved for modern databases via the command  ALTER TABLE transaction ALTER COLUMN from_wallet_id DROP NOT NULL;

so thats why , inside the env.py for each run_migrations function , i added an additional keyword arg render_as_batch=True inside context.configure 