# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import CliCommandType
from azure.cli.core.commands.arm import show_exception_handler
from ._client_factory import (cf_sa, cf_sa_preview, cf_blob_data_gen_update,
                              blob_data_service_factory, adls_blob_data_service_factory)
from .profiles import CUSTOM_DATA_STORAGE, CUSTOM_MGMT_STORAGE, CUSTOM_MGMT_PREVIEW_STORAGE, CUSTOM_DATA_STORAGE_ADLS


def load_command_table(self, _):  # pylint: disable=too-many-locals, too-many-statements
    storage_account_sdk = CliCommandType(
        operations_tmpl='azext_storage_preview.vendored_sdks.azure_mgmt_storage.operations.storage_accounts_operations'
                        '#StorageAccountsOperations.{}',
        client_factory=cf_sa,
        resource_type=CUSTOM_MGMT_STORAGE
    )

    storage_account_custom_type = CliCommandType(
        operations_tmpl='azext_storage_preview.operations.account#{}',
        client_factory=cf_sa)

    def get_custom_sdk(custom_module, client_factory, resource_type=CUSTOM_DATA_STORAGE):
        """Returns a CliCommandType instance with specified operation template based on the given custom module name.
        This is useful when the command is not defined in the default 'custom' module but instead in a module under
        'operations' package."""
        return CliCommandType(
            operations_tmpl='azext_storage_preview.operations.{}#'.format(custom_module) + '{}',
            client_factory=client_factory,
            resource_type=resource_type
        )

    with self.command_group('storage account', storage_account_sdk, resource_type=CUSTOM_MGMT_STORAGE,
                            custom_command_type=storage_account_custom_type) as g:
        g.command('check-name', 'check_name_availability')
        g.custom_command('create', 'create_storage_account', min_api='2016-01-01')
        g.command('delete', 'delete', confirmation=True)
        g.show_command('show', 'get_properties')
        g.custom_command('list', 'list_storage_accounts')
        g.custom_command('show-usage', 'show_storage_account_usage', min_api='2018-02-01')
        g.generic_update_command('update', getter_name='get_properties', setter_name='update',
                                 custom_func_name='update_storage_account', min_api='2016-12-01')
        g.command('keys renew', 'regenerate_key', transform=lambda x: getattr(x, 'keys', x))
        g.command('keys list', 'list_keys', transform=lambda x: getattr(x, 'keys', x))
        failover_confirmation = """
The secondary cluster will become the primary cluster after failover. Please understand the following impact to your storage account before you initiate the failover:
    1. Please check the Last Sync Time using `az storage account show` with `--expand geoReplicationStats` and check the "geoReplicationStats" property. This is the data you may lose if you initiate the failover.
    2. After the failover, your storage account type will be converted to locally redundant storage (LRS). You can convert your account to use geo-redundant storage (GRS).
    3. Once you re-enable GRS for your storage account, Microsoft will replicate data to your new secondary region. Replication time is dependent on the amount of data to replicate. Please note that there are bandwidth charges for the bootstrap. Please refer to doc: https://azure.microsoft.com/pricing/details/bandwidth/
"""
        g.command('failover', 'failover', supports_no_wait=True,
                  confirmation=failover_confirmation)

    with self.command_group('storage account network-rule', storage_account_sdk,
                            custom_command_type=storage_account_custom_type,
                            resource_type=CUSTOM_MGMT_STORAGE, min_api='2017-06-01') as g:
        g.custom_command('add', 'add_network_rule')
        g.custom_command('list', 'list_network_rules')
        g.custom_command('remove', 'remove_network_rule')

    storage_account_sdk_preview = CliCommandType(
        operations_tmpl='azext_storage_preview.vendored_sdks.azure_mgmt_preview_storage.operations.'
                        'storage_accounts_operations#StorageAccountsOperations.{}',
        client_factory=cf_sa_preview,
        resource_type=CUSTOM_MGMT_PREVIEW_STORAGE
    )

    storage_account_custom_preview_type = CliCommandType(
        operations_tmpl='azext_storage_preview.operations.account#{}',
        client_factory=cf_sa_preview)

    with self.command_group('storage account management-policy', storage_account_sdk_preview,
                            resource_type=CUSTOM_MGMT_PREVIEW_STORAGE,
                            custom_command_type=storage_account_custom_preview_type) as g:
        g.show_command('show', 'get_management_policies')
        g.custom_command('create', 'create_management_policies')
        g.generic_update_command('update', getter_name='get_management_policies',
                                 setter_name='update_management_policies',
                                 setter_type=storage_account_custom_type)
        g.command('delete', 'delete_management_policies')

    base_blob_sdk = CliCommandType(
        operations_tmpl='azext_storage_preview.vendored_sdks.azure_storage.blob.baseblobservice#BaseBlobService.{}',
        client_factory=blob_data_service_factory,
        resource_type=CUSTOM_DATA_STORAGE)

    with self.command_group('storage blob service-properties', command_type=base_blob_sdk) as g:
        g.storage_command_oauth('show', 'get_blob_service_properties', exception_handler=show_exception_handler)
        g.storage_command_oauth('update', generic_update=True, getter_name='get_blob_service_properties',
                                setter_type=get_custom_sdk('blob', cf_blob_data_gen_update),
                                setter_name='set_service_properties',
                                client_factory=cf_blob_data_gen_update)

    block_blob_sdk = CliCommandType(
        operations_tmpl='azure.multiapi.storage.blob.blockblobservice#BlockBlobService.{}',
        client_factory=blob_data_service_factory,
        resource_type=CUSTOM_DATA_STORAGE)

    with self.command_group('storage azcopy blob', command_type=block_blob_sdk,
                            custom_command_type=get_custom_sdk('azcopy', blob_data_service_factory)) as g:
        g.storage_custom_command_oauth('upload', 'storage_blob_upload')
        g.storage_custom_command_oauth('download', 'storage_blob_download')
        g.storage_custom_command_oauth('delete', 'storage_blob_remove')
        g.storage_custom_command_oauth('sync', 'storage_blob_sync')

    with self.command_group('storage azcopy', custom_command_type=get_custom_sdk('azcopy', None)) as g:
        g.custom_command('run-command', 'storage_run_command', validator=lambda namespace: None)

    # pylint: disable=line-too-long
    adls_base_blob_sdk = CliCommandType(
        operations_tmpl='azext_storage_preview.vendored_sdks.azure_adls_storage_preview.blob.baseblobservice#BaseBlobService.{}',
        client_factory=adls_blob_data_service_factory,
        resource_type=CUSTOM_DATA_STORAGE_ADLS)

    # New commands for ADLS Gen2
    # Blob Pipeline
    with self.command_group('storage blob', command_type=adls_base_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', adls_blob_data_service_factory,
                                                               CUSTOM_DATA_STORAGE_ADLS),
                            resource_type=CUSTOM_DATA_STORAGE_ADLS) as g:
        from ._format import transform_blob_output
        from ._transformers import transform_storage_list_output
        g.storage_custom_command_oauth('move', 'rename_directory')
        g.storage_command_oauth('list', 'list_blobs', transform=transform_storage_list_output,
                                table_transformer=transform_blob_output)
        g.storage_custom_command_oauth('show', 'show_blob')

    with self.command_group('storage blob access', command_type=adls_base_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', adls_blob_data_service_factory,
                                                               CUSTOM_DATA_STORAGE_ADLS),
                            resource_type=CUSTOM_DATA_STORAGE_ADLS) as g:
        g.storage_custom_command_oauth('set', 'rename_directory')
        g.storage_custom_command_oauth('update', 'show_blob')

    # Blob directory Pipeline
    with self.command_group('storage blob directory', command_type=adls_base_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', adls_blob_data_service_factory,
                                                               CUSTOM_DATA_STORAGE_ADLS),
                            resource_type=CUSTOM_DATA_STORAGE_ADLS) as g:
        from ._format import transform_blob_output
        from ._transformers import (transform_storage_list_output, create_boolean_result_output_transformer)
        g.storage_command_oauth('create', 'create_directory')
        g.storage_command_oauth('delete', 'delete_directory')
        g.storage_custom_command_oauth('move', 'rename_directory')
        g.storage_custom_command_oauth('show', 'show_directory', table_transformer=transform_blob_output,
                                       exception_handler=show_exception_handler)
        g.storage_custom_command_oauth('list', 'list_directory', transform=transform_storage_list_output,
                                       table_transformer=transform_blob_output)
        g.storage_command_oauth('exists', 'exists', transform=create_boolean_result_output_transformer('exists'))
        g.storage_command_oauth(
            'metadata show', 'get_blob_metadata', exception_handler=show_exception_handler)
        g.storage_command_oauth('metadata update', 'set_blob_metadata')

    with self.command_group('storage blob directory',
                            custom_command_type=get_custom_sdk('azcopy', blob_data_service_factory)) as g:
        g.storage_custom_command_oauth('upload', 'storage_blob_upload')
        g.storage_custom_command_oauth('download', 'storage_blob_download')

    with self.command_group('storage blob directory access', command_type=adls_base_blob_sdk,
                            custom_command_type=get_custom_sdk('blob', adls_blob_data_service_factory,
                                                               CUSTOM_DATA_STORAGE_ADLS),
                            resource_type=CUSTOM_DATA_STORAGE_ADLS) as g:
        g.storage_command_oauth('set', 'set_path_access_control')
        g.storage_command_oauth('update', 'set_path_access_control')
        g.storage_command_oauth('show', 'get_path_access_control')
