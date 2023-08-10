"""
This module contains functions to send NFTs to users who completed a quest and won an NFT airdrop.
Functions

get_nft_winners()
Get the list of the NFT winners.

get_smr_address_submitters(status: str)
Returns a list of submitters for a given status of SMR address.

get_smr_address_from_quest_completers()
Retrieves the SMR addresses of users who completed a quest and won an NFT airdrop.

send_to_address(addresses: list)
Sends NFTs to the addresses, if addresses are present.


Note: The module imports the following variables and functions from the tools module:
get_zealy_api_data, return_valid_shimmer_addresses, logger, basic_checks, create_shimmer_profile,
get_available_nfts, send_nfts, check_if_sent, unique_addresses, subdomain, x_api_key,
nft_drop_quest_id, smr_address_quest_id, validate_zealy_api_data, validate_shimmer_address,
shimmer_address_hrp, collection_nft_id, mint_nfts, delta_days.
"""
import time
from datetime import datetime, timedelta
import multiprocessing
import re
from tools import (get_zealy_api_data, return_valid_shimmer_addresses, logger,
                   basic_checks, create_shimmer_profile, get_available_nfts,
                   send_nfts, check_if_sent, unique_addresses, subdomain, x_api_key,
                   nft_drop_quest_id, smr_address_quest_id, validate_zealy_api_data,
                   validate_shimmer_address, shimmer_address_hrp, collection_nft_id,
                   mint_nfts)

##########################
# Start
##########################


def get_nft_winners():
    """
    This function retrieves the list of the winners of the NFT airdrop by
    querying the Zealy API with a specific quest ID and status.
    Returns a list of user IDs who completed the NFT airdrop quest successfully.

    Args:
    None

    Returns:
    list: A list of user IDs who successfully completed the NFT airdrop quest.

    Example:
    >>> get_nft_winners()
    [123, 456, 789]
    """
    try:
      logger.info("Get the list of the NFT winners")
      status = "success"
      nft_airdrop_quest_completers = get_zealy_api_data(
          subdomain,
          x_api_key,
          nft_drop_quest_id,
          status
          )
      nft_airdrop_user_ids = []
      for item in nft_airdrop_quest_completers['data']:
          nft_airdrop_user_id = item['user']['id']
          nft_airdrop_user_ids.append(nft_airdrop_user_id)
      logger.debug("nft_airdrop_user_ids %s", nft_airdrop_user_ids)
      return nft_airdrop_user_ids
    except Exception as e:
      logger.warning("An error occurred in get_nft_winners(): %s", e)
      sleep(300)
      continue

def get_smr_address_submitters(status):
    """
    Returns a list of submitters for a given status of SMR address.

    Args:
    - status (str): The status of the SMR submission quest on Zealy.

    Returns:
    - submitters (list): A list of submitters for the given status.

    Example:
    get_smr_address_submitters('success')  # Returns ['43289723890', '3290480239']
    """
    try:
      logger.info("Query Zealy for submitted addresses")
      smr_address_quest_completers = get_zealy_api_data(
          subdomain,
          x_api_key,
          smr_address_quest_id,
          status
          )
      smr_address_submitters = []
      for item in smr_address_quest_completers['data']:
          smr_address_user_id = item['user']['id']
          smr_address = item['submission']['value']
          # Remove any excessive characters/text from possible input
          match = re.search(r"smr1\w+", smr_address)
          if match:
              smr_address = match.group()
          else:
              continue
          smr_address_user_object = (smr_address_user_id, smr_address)
          smr_address_submitters.append(smr_address_user_object)
  
      logger.debug("smr_address_submitters %s", smr_address_submitters)
      return smr_address_submitters
      
    except Exception as e:
      logger.warning("An error occurred in get_smr_address_submitters(): %s", e)
      sleep(300)
      continue

def get_smr_address_from_quest_completers():
    """
    Retrieves the SMR addresses of users who completed a quest and won an NFT airdrop.

    This function first retrieves the list of NFT winners through the `get_nft_winners()` function.
    It then calls the `get_smr_address_submitters()` function with a status of "success" to get
    the SMR addresses of users who successfully submitted their addresses for the airdrop.

    Returns:
    -------
    list of str:
        A list of SMR addresses of users who completed the quest and won the NFT airdrop.
    """
    try:
      logger.info("Get %s address from the quest completers", shimmer_address_hrp)
      nft_airdrop_quest_completers = get_nft_winners()
      logger.debug("NFT Winners %s", nft_airdrop_quest_completers)
  
      smr_address_quest_completers = get_smr_address_submitters(status="success")
      logger.debug("Address Submitters %s", smr_address_quest_completers)
  
      # Iterate over each element in smr_address_submitters
      smr_addresses = []
      for submitter in smr_address_quest_completers:
          user_id, smr_address = submitter
          # Check if the discord ID is in nft_airdrop_user_ids
          if user_id in nft_airdrop_quest_completers:
              # If it is, append the SMR address to the smr_addresses list
              smr_addresses.append(smr_address)
      logger.debug("appended addresses %s", smr_addresses)
      smr_addresses = unique_addresses(smr_addresses)
      logger.debug("unique addresses %s", smr_addresses)
      return smr_addresses
      
    except Exception as e:
      logger.warning("An error occurred in get_smr_address_from_quest_completers(): %s", e)
      sleep(300)
      continue
      
def send_to_address(addresses):
    """Send NFTs to the provided addresses, if any.

    Args:
        addresses (list): A list of string values representing the addresses of recipients.

    Returns:
        None

    Logs:
        Logs the following information at the info level:
            - 'Sending NFTs to the addresses, if addresses are present'
            - 'No addresses provided' if the addresses argument is empty
            - 'Amount of addresses: %s' with the length of addresses as the parameter
    """
    logger.info("Sending NFTs to the addresses, if addresses are present")
    if not addresses:
        logger.info("No addresses provided")
        return

    logger.info("Amount of addresses: %s",len(addresses))
    invalid_rows = []

    # Generate unixtimestamp for the expiry condition
    # Get the current time
    now = datetime.now()

    # Add one year to the current time
    one_year_from_now = now + timedelta(days=int(365))
    six_months_from_now = now + timedelta(days=int(183))

    # Convert the datetime object to Unix timestamp
    expiration_unixtime = int(time.mktime(one_year_from_now.timetuple()))
    timelock_unixtime = int(time.mktime(six_months_from_now.timetuple()))


    # Define the outputs array
    outputs = []

    nft_ids = get_available_nfts() # get all available NFT IDs
    logger.debug("Available NFTs: %s", len(nft_ids))

    # remove 1 to account for the available collection NFT id
    while len(addresses) > (len(nft_ids) - 1):
        num_missing_nfts = len(addresses) - (len(nft_ids) - 1)
        logger.warning(
            "Not enough available NFTs for all addresses. Minting %s more NFTs",
            num_missing_nfts
            )
        logger.debug("Required NFTS: %s", num_missing_nfts)
        mint_nfts(num_missing_nfts)
        nft_ids = get_available_nfts() # update the available NFT IDs
        logger.info("Available NFTs: %s", len(nft_ids))

    # Split addresses into chunks of 10 addresses
    chunks = [addresses[i:i+10] for i in range(0, len(addresses), 10)]

    for chunk in chunks:
        for address in chunk:
            try:
                while True:
                    nft_id = nft_ids.pop(0)  # get and remove the first available NFT ID
                    if nft_id == collection_nft_id:
                        logger.warning("Skipping NFT ID %s for address %s",
                                        collection_nft_id,
                                        address
                                       )
                        continue
                    logger.debug("Address: %s", address)
                    logger.debug("NFT ID: %s", nft_id)
                    logger.debug("Expiration time: %s", expiration_unixtime)
                    logger.debug("Timelock time: %s", timelock_unixtime)
                    outputs.append(
                        {
                        "amount": "0",
                        "recipientAddress": address,
                        "unlocks":
                            {
                              "expirationUnixTime": expiration_unixtime,
                              "timelockUnixTime": timelock_unixtime,
                            },
                        "storageDeposit":
                            {
                            "returnStrategy": "Gift",
                            },
                        "assets":
                        {
                        "nftId": nft_id,
                        },
                        }
                    )
                    break  # Exit the loop once a valid NFT ID is found
            except IndexError:
                logger.warning("No more available NFTs for address %s", address)
                invalid_rows.append(address)

        # Call send_smr_tokens with the outputs array
        logger.debug("Prepared Outputs Chunk: %s", outputs)
        send_nfts(outputs)
        # Reset the outputs array for the next chunk
        outputs = []

def get_smr_address_from_quest_and_verify():
    """
    Get the Shimmer (SMR) address from address submission quest and verify.

    This function gets the SMR address from the address submission quest and
    verifies it. It repeatedly polls the Zealy API for new submissions in
    the quest, validates the submitted addresses and marks them as valid or
    invalid accordingly. The function waits for 2 minutes before polling again
    if there are no new submissions in the quest.
    If a valid SMR address is found, it is returned.

    Returns:
    -------
    str
        The valid SMR address if it is found in the quest, otherwise None.
    """
    logger.info(
        "Get %s address from address submission quest",
        shimmer_address_hrp
        )
    while True:
        smr_address_quest_completers = get_zealy_api_data(
            subdomain,
            x_api_key,
            smr_address_quest_id,
            status="pending"
            )
        smr_address_submitters = []
        valid_addresses_quest_ids = []
        invalid_addresses_quest_ids = []
        if not smr_address_quest_completers:
            return

        # Iterate over submissions and validate shimmer addresses
        for item in smr_address_quest_completers['data']:
            smr_address_submission_id = item['id']
            smr_address = item['submission']['value']
            smr_address_user_object = (smr_address_submission_id, smr_address)
            smr_address_submitters.append(smr_address_user_object)

            # Validate the address
            logger.debug(smr_address)
            for address in smr_address.split():
                logger.debug(address)
                if validate_shimmer_address(address):
                    valid_addresses_quest_ids.append(smr_address_submission_id)
                else:
                    invalid_addresses_quest_ids.append(smr_address_submission_id)

            logger.debug("valid addresses %s", valid_addresses_quest_ids)
            logger.debug("invalid addresses  %s", invalid_addresses_quest_ids)

        # Make post request to the API
        if valid_addresses_quest_ids:
            comment = "Thank you for submitting a valid Shimmer address."
            status = "success"
            valid_data = validate_zealy_api_data(
                subdomain,
                x_api_key,
                valid_addresses_quest_ids,
                status,
                comment
                )
            logger.debug(valid_data)

        if invalid_addresses_quest_ids:
            comment = f"Thank you, but the submitted address is not a valid Shimmer address. A valid address starts with {shimmer_address_hrp}. Download the official Shimmer Firefly wallet from https://firefly.iota.org and submit a new address."
            status = "fail"
            invalid_data = validate_zealy_api_data(
                subdomain,
                x_api_key,
                invalid_addresses_quest_ids,
                status,
                comment
                )
            logger.debug(invalid_data)

        time.sleep(2 * 60)  # Pause the script for 15 minutes

def run_nft_dropper():
    """
    Runs the NFT dropper process.

    It checks if the basic information has been filled out in the .env file and 
    creates a Shimmer profile. Then, it checks if new addresses have been submitted 
    and verifies the Shimmer addresses. Finally, it sends NFTs to valid addresses.
    The script sleeps for 2 minutes between each iteration.

    Returns:
        None
    """
    logger.info("Running NFT dropper process")
    if basic_checks():
        logger.info("Basic checks completed")
    else:
        logger.info(
        "Make sure to fill out the information in the .env file. Rename .env.exmple to .env first."
        )
    create_shimmer_profile()
    while True:
        smr_address = check_if_sent(get_smr_address_from_quest_completers())
        logger.debug(("These are new addresses %s", smr_address))

        smr_address = return_valid_shimmer_addresses(smr_address)
        send_to_address(smr_address)
        time.sleep(2 * 60)  # Pause the script for 15 minutes

if __name__ == "__main__":
    logger.info("Starting processes")
    # Create processing for the bot and the richlist generation
    process_one = multiprocessing.Process(target=run_nft_dropper)
    process_two = multiprocessing.Process(target=get_smr_address_from_quest_and_verify)

    # Start the processs
    process_one.start()
    process_two.start()
