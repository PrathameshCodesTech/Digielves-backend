from typing import List

from digielves_setup.models import EmployeePersonalDetails, OutsiderUser, TaskStatus

def get_status_ids_from_creater_side(user_id: int, showCompleter: bool = False) -> List[int]:
    """
    Get the IDs of TaskStatus objects with specific fixed states for a given user's organization.

    Args:
    user_id (int): The ID of the user.

    Returns:
    List[int]: A list of TaskStatus IDs.
    """
    fixed_state_mapping = {
        "Closed": "Closed",
        "Client Action Pending": "Client Action Pending",
        "InReview" : "InReview"
    }

    if showCompleter:
        fixed_state_mapping["Completed"] = "Completed"
    fixed_states_to_include = list(fixed_state_mapping.values())
    try:
        organization_id = EmployeePersonalDetails.objects.get(user_id=user_id).organization_id
    except:
        outsiders = OutsiderUser.objects.get(related_id=user_id)
        organization_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by).organization_id

    fixed_state_ids = list(
        TaskStatus.objects.filter(
            fixed_state__in=fixed_states_to_include,
            organization=organization_id
        ).order_by('order').values_list('id', flat=True)
    )

    return fixed_state_ids


def get_status_ids_from_assigned_side(user_id: int,showCompleter: bool = False) -> List[int]:
    """
    Get the IDs of TaskStatus objects with specific fixed states for a given user's organization.

    Args:
    user_id (int): The ID of the user.
    showCompleter (bool): Flag to include the 'Completed' status. Defaults to False.

    Returns:
    List[int]: A list of TaskStatus IDs.
    """
    fixed_state_mapping = {
            "Pending": "Pending",
            "InProgress": "InProgress",
            "OnHold" : "OnHold"
            }
    
    if showCompleter:
        fixed_state_mapping["Completed"] = "Completed"

    fixed_states_to_include = list(fixed_state_mapping.values())
    
    try:
        organization_id = EmployeePersonalDetails.objects.get(user_id=user_id).organization_id
    except:
        outsiders = OutsiderUser.objects.get(related_id=user_id)
        organization_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by).organization_id

    fixed_state_ids = list(
        TaskStatus.objects.filter(
            fixed_state__in=fixed_states_to_include,
            organization=organization_id
        ).order_by('order').values_list('id', flat=True)
    )

    return fixed_state_ids


def get_completed_status_id(user_id: int,showCompleter: bool = False) -> List[int]:
    """
    Get the IDs of TaskStatus objects with specific fixed states for a given user's organization.

    Args:
    user_id (int): The ID of the user.
    showCompleter (bool): Flag to include the 'Completed' status. Defaults to False.

    Returns:
    List[int]: A list of TaskStatus IDs.
    """
    fixed_state_mapping = {
            "Pending": "Pending",
            "InProgress": "InProgress",
            "OnHold" : "OnHold"
            }
    
    if showCompleter:
        fixed_state_mapping["Completed"] = "Completed"

    fixed_states_to_include = list(fixed_state_mapping.values())
    
    try:
        organization_id = EmployeePersonalDetails.objects.get(user_id=user_id).organization_id
    except:
        outsiders = OutsiderUser.objects.get(related_id=user_id)
        organization_id = EmployeePersonalDetails.objects.get(user_id=outsiders.added_by).organization_id

    fixed_state_ids = list(
        TaskStatus.objects.filter(
            fixed_state__in=fixed_states_to_include,
            organization=organization_id
        ).order_by('order').values_list('id', flat=True)
    )

    return fixed_state_ids

