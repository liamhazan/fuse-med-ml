import pandas as pd
import os
from typing import Callable, Optional
from typing import Tuple

# from MedicalAnalyticsCore.DatabaseUtils.selected_studies_queries import get_annotations_and_findings
# from MedicalAnalyticsCore.DatabaseUtils.tableResolver import TableResolver
# from MedicalAnalyticsCore.DatabaseUtils.connection import create_homer_engine, Connection
# from MedicalAnalyticsCore.DatabaseUtils import tableNames
# from MedicalAnalyticsCore.DatabaseUtils import db_utils as db


# from autogluon.tabular import TabularPredictor
from fuse_examples.classification.multimodality.dataset import IMAGING_TABULAR_dataset
from fuse.data.dataset.dataset_default import FuseDatasetDefault

from fuse_examples.classification.MG_CMMD.input_processor import FuseMGInputProcessor
from fuse.data.processor.processor_dataframe import FuseProcessorDataFrame


from typing import Dict, List
import torch
from fuse.utils.utils_hierarchical_dict import FuseUtilsHierarchicalDict

class PostProcessing:
    def __init__(self, continuous_tabular_features_lst: List,
                 categorical_tabular_features_lst: List,
                 label_lst: List,
                 imaging_features_lst: List,
                 non_imaging_features_lst: List,
                 use_imaging: bool,
                 use_non_imaging: bool):
        self.continuous_tabular_features_lst = continuous_tabular_features_lst
        self.categorical_tabular_features_lst = categorical_tabular_features_lst
        self.label_lst = label_lst
        self.imaging_features_lst = imaging_features_lst
        self.non_imaging_features_lst = non_imaging_features_lst
        self.use_imaging = use_imaging
        self.use_non_imaging = use_non_imaging

    def __call__(self, batch_dict: Dict) -> Dict:
        if not self.use_imaging and not self.use_non_imaging:
            raise ValueError('No features are in use')
        mask_list = self.use_imaging * self.imaging_features_lst + self.use_non_imaging * self.non_imaging_features_lst
        mask_continuous = torch.zeros(len( self.continuous_tabular_features_lst))
        for i in range(len(mask_list)):
            try:
                mask_continuous[self.continuous_tabular_features_lst.index(mask_list[i])] = 1
            except:
                pass
        mask_categorical = torch.zeros(len( self.categorical_tabular_features_lst))
        for i in range(len(mask_list)):
            try:
                mask_categorical[self.categorical_tabular_features_lst.index(mask_list[i])] = 1
            except:
                pass
        categorical = [FuseUtilsHierarchicalDict.get(batch_dict, 'data.' + feature_name) for feature_name in self.categorical_tabular_features_lst]
        for i in range(len(categorical)):
            if categorical[i].dim() == 0:
                categorical[i] = torch.unsqueeze(categorical[i], 0)
        categorical_tensor = torch.cat(tuple(categorical), 0)
        categorical_tensor = categorical_tensor.float()
        categorical_tensor = torch.mul(categorical_tensor, mask_categorical)
        FuseUtilsHierarchicalDict.set(batch_dict, 'data.categorical', categorical_tensor.float())
        continuous = [FuseUtilsHierarchicalDict.get(batch_dict, 'data.' + feature_name) for feature_name in self.continuous_tabular_features_lst]
        for i in range(len(continuous)):
            if continuous[i].dim() == 0:
                continuous[i] = torch.unsqueeze(continuous[i], 0)
        continuous_tensor = torch.cat(tuple(continuous), 0)
        continuous_tensor = continuous_tensor.float()
        continuous_tensor = torch.mul(continuous_tensor, mask_continuous)
        FuseUtilsHierarchicalDict.set(batch_dict, 'data.continuous', continuous_tensor.float())
        label = FuseUtilsHierarchicalDict.get(batch_dict, 'data.' + self.label_lst[0])
        FuseUtilsHierarchicalDict.set(batch_dict, 'data.' + self.label_lst[0], label.long())
        feature_lst = self.continuous_tabular_features_lst + self.categorical_tabular_features_lst
        for feature in feature_lst:
            FuseUtilsHierarchicalDict.pop(batch_dict, 'data.' + feature)
        return batch_dict


# feature selection univarient analysis

#-------------------Tabular
def get_selected_features_mg(data,features_mode,key_columns):
    features_dict = tabular_feature_mg()
    columns_names = list(data.columns)
    if features_mode == 'full':
        selected_col = \
            features_dict['continuous_clinical_feat'] + \
            features_dict['categorical_clinical_feat']

    selected_col = selected_col + key_columns
    selected_colIx = [columns_names.index(selected_col[i]) for i in range(len(selected_col))]
    return selected_col,selected_colIx


def tabular_feature_mg():
    features_dict = {}

    features_dict['continuous_clinical_feat'] = ['findings_size', 'findings_x_max', 'findings_y_max', 'DistanceSourceToPatient',
                                         'DistanceSourceToDetector', 'x_pixel_spacing', 'XRayTubeCurrent', 'CompressionForce',
                                         'exposure_time', 'KVP', 'body_part_thickness', 'RelativeXRayExposure', 'exposure_in_mas',
                                         'age'] #14 continuous clinical features
    features_dict['categorical_clinical_feat'] = ['side', 'is_distortions', 'is_spiculations', 'is_susp_calcifications',
                                         'breast_density_1', 'breast_density_2', 'breast_density_3',
                                         'breast_density_4', 'final_side_birad_0', 'final_side_birad_1',
                                         'final_side_birad_2', 'final_side_birad_3', 'final_side_birad_4',
                                         'final_side_birad_5', 'final_side_birad_6', 'final_side_birad_7',
                                         'final_side_birad_8', 'birad_0', 'birad_1', 'birad_2', 'birad_3', 'birad_4',
                                         'birad_5', 'birad_6', 'birad_7', 'birad_8', 'calcification_0',
                                         'calcification_1', 'calcification_2', 'calcification_3', 'calcification_4',
                                         'calcification_5', 'calcification_6', 'calcification_7', 'calcification_8',
                                         'calcification_9', 'longitudinal_change_0', 'longitudinal_change_1',
                                         'longitudinal_change_2', 'longitudinal_change_3', 'longitudinal_change_4',
                                         'type_0', 'type_1', 'type_2', 'type_3', 'type_4', 'type_5', 'type_6', 'race_0',
                                         'race_1', 'race_2', 'race_3', 'race_4', 'race_5', 'race_6', 'race_7', 'race_8',
                                         'race_9', 'race_10', 'max_prev_birad_class_0', 'max_prev_birad_class_1',
                                         'max_prev_birad_class_2', 'max_prev_birad_class_3'] #63 categorical clinical features
    features_dict['visual_feat'] = ['findings_size', 'findings_x_max', 'findings_y_max', 'side', 'is_distortions',
                           'is_spiculations', 'is_susp_calcifications',
                           'breast_density_1', 'breast_density_2', 'breast_density_3',
                           'breast_density_4', 'final_side_birad_0', 'final_side_birad_1',
                           'final_side_birad_2', 'final_side_birad_3', 'final_side_birad_4',
                           'final_side_birad_5', 'final_side_birad_6', 'final_side_birad_7',
                           'final_side_birad_8', 'birad_0', 'birad_1', 'birad_2', 'birad_3', 'birad_4',
                           'birad_5', 'birad_6', 'birad_7', 'birad_8', 'calcification_0',
                           'calcification_1', 'calcification_2', 'calcification_3', 'calcification_4',
                           'calcification_5', 'calcification_6', 'calcification_7', 'calcification_8',
                           'calcification_9', 'longitudinal_change_0', 'longitudinal_change_1',
                           'longitudinal_change_2', 'longitudinal_change_3', 'longitudinal_change_4',
                           'type_0', 'type_1', 'type_2', 'type_3', 'type_4', 'type_5', 'type_6',
                           'max_prev_birad_class_0', 'max_prev_birad_class_1', 'max_prev_birad_class_2',
                           'max_prev_birad_class_3']
    features_dict['non_visual_feat'] = ['DistanceSourceToPatient', 'DistanceSourceToDetector', 'x_pixel_spacing',
                               'XRayTubeCurrent',
                               'CompressionForce', 'exposure_time', 'KVP', 'body_part_thickness',
                               'RelativeXRayExposure',
                               'exposure_in_mas', 'age', 'race_0', 'race_1', 'race_2', 'race_3', 'race_4', 'race_5',
                               'race_6', 'race_7', 'race_8', 'race_9', 'race_10']



    return features_dict


def tabular_mg(tabular_filename,key_columns):
    data = pd.read_csv(tabular_filename)
    column_names,column_colIx = get_selected_features_mg(data, 'full',key_columns)
    df_tabular = data[column_names]
    return df_tabular


#------------------Imaging
def imaging_mg(imaging_filename,key_columns):
    label_column = 'finding_biopsy'
    img_sample_column = 'dcm_url'

    if os.path.exists(imaging_filename):
        df = pd.read_csv(imaging_filename)
    else:
        REVISION_DATE = '20200915'
        TableResolver().set_revision(REVISION_DATE)
        revision = {'prefix': 'sentara', 'suffix': REVISION_DATE}
        engine = Connection().get_engine()

        df_with_findings = get_annotations_and_findings(engine, revision,
                                                        exam_types=['MG'], viewpoints=None,  # ['CC','MLO'], \
                                                        include_findings=True, remove_invalids=True,
                                                        remove_heldout=False, \
                                                        remove_excluded=False, remove_less_than_4views=False, \
                                                        load_from_file=False, save_to_file=False)

        # dicom_table = db.get_table_as_dataframe(engine, tableNames.get_dicom_tags_table_name(revision))
        # study_statuses = db.get_table_as_dataframe(engine, tableNames.get_study_statuses_table_name(revision))
        my_providers = ['sentara']
        df = df_with_findings.loc[df_with_findings['provider'].isin(my_providers)]
        # fixing assymetry
        asymmetries = ['asymmetry', 'developing asymmetry', 'focal asymmetry', 'global asymmetry']
        df['is_asymmetry'] = df['pathology'].isin(asymmetries)
        df['is_Breast_Assymetry'] = df['type'].isin(['Breast Assymetry'])
        df.loc[df['is_asymmetry'], 'pathology'] = df[df['is_asymmetry']]['biopsy_outcome']
        df.loc[df['is_Breast_Assymetry'], 'pathology'] = df[df['is_Breast_Assymetry']]['biopsy_outcome']
        # remove duble xmls
        aa_unsorted = df
        aa_unsorted.sort_values('xml_url', ascending=False, inplace=True)
        xml_url_to_keep = aa_unsorted.groupby(['image_id'])['xml_url'].transform('first')
        df = aa_unsorted[aa_unsorted['xml_url'] == xml_url_to_keep]
        remove_from_pathology = ['undefined', 'not_applicable', 'Undefined', 'extracapsular rupture of breast implant',
                                 'intracapsular rupture of breast implant']
        is_pathology = ~df.pathology.isnull() & ~df.pathology.isin(remove_from_pathology)
        is_digital = df.image_source == 'Digital'
        is_biopsy = df.finding_biopsy.isin(['negative', 'negative high risk', 'positive'])
        df = df[(is_digital) & (is_pathology) & (is_biopsy)]
        df.to_csv(imaging_filename)

    df1 = df.groupby(key_columns)[img_sample_column].apply(lambda x:  list(map(str, x))).reset_index()
    df2 = df.groupby(key_columns)[label_column].apply(lambda x:  list(map(str, x))).reset_index()


    return pd.merge(df1,df2,on=key_columns)


#------------------Imaging+Tabular
def merge_datasets(tabular_filename,imaging_filename,key_columns):
    tabular_data = tabular_mg(tabular_filename, key_columns)
    imaging_data = imaging_mg(imaging_filename, key_columns)
    tabular_data[key_columns] = tabular_data[key_columns].astype(str)
    imaging_data[key_columns] = imaging_data[key_columns].astype(str)
    tabular_columns = tabular_data.columns.values
    imaging_columns = imaging_data.columns.values
    dataset = pd.merge(tabular_data, imaging_data, on=key_columns, how='inner')
    return dataset,tabular_columns,imaging_columns

#------------------Baseline
def apply_gluon_baseline(train_set,test_set,label,save_path):

    predictor = TabularPredictor(label=label, path=save_path, eval_metric='roc_auc').fit(train_set)
    results = predictor.fit_summary(show_plot=True)

    # Inference time:
    y_test = test_set[label]
    test_data = test_set.drop(labels=[label],
                               axis=1)  # delete labels from test data since we wouldn't have them in practice
    print(test_data.head())

    predictor = TabularPredictor.load(
        save_path)
    y_pred = predictor.predict_proba(test_data)
    perf = predictor.evaluate_predictions(y_true=y_test, y_pred=y_pred, auxiliary_metrics=True)

#MO: thinkabout specific name
def MG_dataset(tabular_filename:str,
               imaging_filename:str,
               train_val_test_filenames:list,

               #Mo: internal parameters
               imaging_processor,
               tabular_processor,

               key_columns:list,
               label_key:str,
               img_key:str,
               sample_key: str,

               cache_dir: str = 'cache',
               reset_cache: bool = False,
               post_cache_processing_func: Optional[Callable] = None) -> Tuple[FuseDatasetDefault, FuseDatasetDefault]:


    dataset, tabular_columns, imaging_columns = merge_datasets(tabular_filename, imaging_filename, key_columns)

    dataset['finding_biopsy'] = [1 if 'positive' in sample else 0 for sample in list(dataset[label_key])]
    dataset = dataset.loc[:, ~dataset.columns.duplicated()]
    dataset.rename(columns={'patient_id': sample_key}, inplace=True)

    train_set = dataset[dataset[sample_key].isin(pd.read_csv(train_val_test_filenames[0])['patient_id'])]
    val_set = dataset[dataset[sample_key].isin(pd.read_csv(train_val_test_filenames[1])['patient_id'])]
    test_set = dataset[dataset[sample_key].isin(pd.read_csv(train_val_test_filenames[2])['patient_id'])]

    features_list = list(tabular_columns)
    [features_list.remove(x) for x in key_columns]
    train_dataset, validation_dataset, test_dataset = IMAGING_TABULAR_dataset(
                                                                        df=[train_set, val_set, test_set],
                                                                        imaging_processor=imaging_processor,
                                                                        tabular_processor=tabular_processor,
                                                                        label_key=label_key,
                                                                        img_key=img_key,
                                                                        tabular_features_lst=features_list + [label_key] + [sample_key],
                                                                        sample_key=sample_key,
                                                                        cache_dir=cache_dir,
                                                                        reset_cache=reset_cache,
                                                                        post_cache_processing_func=post_cache_processing_func
                                                                        )

    return train_dataset, validation_dataset, test_dataset



if __name__ == "__main__":
    data_path = '/projects/msieve_dev3/usr/Tal/my_research/multi-modality/mg_radiologist_usa/'
    tabular_filename = os.path.join(data_path, 'dataset_MG_clinical.csv')
    imaging_filename = os.path.join(data_path, 'mg_usa_cohort.csv')

    train_val_test_filenames = [os.path.join(data_path, 'dataset_MG_clinical_train.csv'),
                                os.path.join(data_path, 'dataset_MG_clinical_validation.csv'),
                                os.path.join(data_path, 'dataset_MG_clinical_heldout.csv'), ]

    key_columns = ['patient_id']
    fuse_key_column = 'sample_desc'
    label_column = 'finding_biopsy'
    img_sample_column = 'dcm_url'
    train_dataset, validation_dataset, test_dataset = \
                                                    MG_dataset(tabular_filename=tabular_filename,
                                                               imaging_filename=imaging_filename,
                                                               train_val_test_filenames=train_val_test_filenames,
                                                               key_columns=key_columns,
                                                               sample_key=fuse_key_column,
                                                               label_key=label_column,
                                                               img_key=img_sample_column,
                                                               cache_dir='./mg_radiologist_usa/',
                                                               reset_cache=False,
                                                               imaging_processor=FuseMGInputProcessor,
                                                               tabular_processor=FuseProcessorDataFrame,
                                                               )


    # apply_gluon_baseline(train_set[tabular_columns+[label_column]],
    #                      test_set[tabular_columns+[label_column]],label_column,'./Results/MG+clinical/gluon_baseline/')