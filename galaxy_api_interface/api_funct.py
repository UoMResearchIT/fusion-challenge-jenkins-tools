from bioblend.galaxy import GalaxyInstance
import json

def call_api(server, api_key, workflow_name, history_name, infiles, outfiles, delete_history=True, workflow_report=False, output_folder='./workflow_output/'):
    """
    Function to call galaxy workflow via API

    Usage:
        call_api(
            server = "http://<server address>",
            api_key = "<api_key>",
            workflow_name = "More Complex Test Workflow",
            history_name = "Complex Test API",
            infiles = ['text_1.txt', 'text_2.txt'],
            outfiles = ['joined_files.txt', 'last_line.txt'],
            delete_history = True,
            workflow_report = True,
            output_folder='./output/'
        )

    Args:
        server (string): Galaxy server address
        api_key (string): User generated string from galaxy instance
            to create: User > Preferences > Manage API Key > Create a new key
        workflow_name (string): Target workflow name
        history_name (string): String to name the history EDIT - will want this tagged with date?
        infiles (array of strings): File paths to the input files
        outfiles (array of strings): File paths to the output files
        delete_history (bool, optional): Whether the history should be deleted from the galaxy instance
            Default: True
        workflow_report (bool, optional): Give a report from the workflow run
            Default: False
        output_folder (string, optional): Folder for the outputs of the workflow to be saved to
            Default: './workflow_output/'

    """

    gi = GalaxyInstance(url=server, key=api_key)

    # Create new history with name history_name
    new_hist = gi.histories.create_history(name=history_name)

    # Upload file to the history
    inputs = {}
    index = 0
    for input in infiles:
        upload = gi.tools.upload_file(input, new_hist["id"])
        # Setup Inputs for the workflow - EDIT - need better way to define which input is which
        inputs[str(index)] = {'id': upload['outputs'][0]['id'], 'src': 'hda'}
        index += 1

    # Get list of workflows, searching for workflow with name workflow_name
    api_test_workflow = gi.workflows.get_workflows(name=workflow_name)

    # Call workflow
    workflow_run = gi.workflows.invoke_workflow(
        workflow_id = api_test_workflow[0]['id'],
        inputs = inputs,
        history_id = new_hist['id']
        )

    # Gets the invocation of the above workflow and then waits for it to complete (need to check max time on this - especially for long sim runs)
    # Also this freezes the py program so still same omni issue of freezing up whole of omni
    # Better soln of the intermediate workflow caller?
    invocation_workflow = gi.invocations.get_invocations(workflow_id=api_test_workflow[0]['id'])
    wait = gi.invocations.wait_for_invocation(invocation_id=invocation_workflow[0]['id'])

    for output in outfiles:
        try:
            # Finds the file in the history that is the output of the workflow
            dataset = gi.datasets.get_datasets(history_id=new_hist['id'], name=output)
            filepath = output_folder + output
            # Saves to local folder
            download = gi.datasets.download_dataset(file_path=filepath, dataset_id=dataset[0]['id'], use_default_filename=False)
        except:
            # EDIT - better error handling needed - works for now...
            print(f'Output "{output}" was not found.')

    if workflow_report:
        download = gi.invocations.get_invocation_biocompute_object(invocation_id=invocation_workflow[0]['id'])
        dict_to_write = json.dumps(download)
        with open(f'{output_folder}Report_{history_name}.json', 'w') as f:
            f.write(dict_to_write)

    # Delete the galaxy history to not clog up storage on the machine
    if delete_history:
        gi.histories.delete_history(history_id=new_hist['id'])

    return True

