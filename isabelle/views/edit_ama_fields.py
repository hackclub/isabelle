from isabelle.utils.env import env
from blockkit import Modal, Input, Checkboxes, RadioButtons, Option, UrlInput


async def get_edit_ama_fields_modal(event_id: str):
    event = await env.database.get_event(event_id)
    if event is None:
        return
    is_ama = event["AMA"]
    ama_avatar = event["AMAAvatar"]

    ama_avatar_input = UrlInput().action_id("ama-avatar")
    if ama_avatar:
        ama_avatar_input.initial_value(ama_avatar)
    

    modal = (
        Modal()
            .title("Edit AMA fields")
            .submit("Change fields")
            .private_metadata(event_id)
            .callback_id("edit_ama_fields")
            .add_block(
                Input("AMA").block_id("ama").element(
                    RadioButtons()
                    .action_id("bool")
                    .add_option(Option("Yes",  "yes"))
                    .add_option(Option("No", "no"))
                    .initial_option(
                        Option("Yes", "yes") if is_ama
                        else Option("No", "no")
                    )
                )
            )
            .add_block(
                Input("AMA Avatar").block_id("amaavatar").element(ama_avatar_input)
            )

    ).build()
    print(modal)
    return modal