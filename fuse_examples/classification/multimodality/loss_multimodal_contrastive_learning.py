from typing import Dict
import torch
import torch.nn.functional as F
from fuse.utils.utils_hierarchical_dict import FuseUtilsHierarchicalDict


def softcrossentropyloss(target, logits):
    """
    From the pytorch discussion Forum:
    https://discuss.pytorch.org/t/soft-cross-entropy-loss-tf-has-it-does-pytorch-have-it/69501
    """
    logprobs = torch.nn.functional.log_softmax(logits, dim=1)
    loss = -(target * logprobs).sum() / logits.shape[0]
    return loss


class FuseLossMultimodalContrastiveLearning:
    def __init__(self,
                 imaging_representations: str = None,
                 tabular_representations: str = None,
                 label: str = None,
                 temperature: float = 1.0,
                 alpha: float = 0.5
                 ) -> None:
        self.imaging_representations = imaging_representations
        self.tabular_representations = tabular_representations
        self.temperature = temperature
        self.label = label
        self.alpha = alpha

    def __call__(self, batch_dict: Dict) -> torch.Tensor:
        # filter batch_dict if required
        imaging_representations = FuseUtilsHierarchicalDict.get(batch_dict, self.imaging_representations)
        tabular_representations = FuseUtilsHierarchicalDict.get(batch_dict, self.tabular_representations)
        label = FuseUtilsHierarchicalDict.get(batch_dict, self.label)
        if len(imaging_representations.shape)<2:
            imaging_representations = imaging_representations.unsqueeze(dim=0)
        if len(imaging_representations.shape) < 2:
            tabular_representations = tabular_representations.unsqueeze(dim=0)
        imaging_representations = F.normalize(imaging_representations, p=2, dim=1)
        tabular_representations = F.normalize(tabular_representations, p=2, dim=1)
        label_vec = torch.unsqueeze(label, 0)
        mask = torch.eq(torch.transpose(label_vec, 0, 1), label_vec).float()
        logits_imaging_tabular = torch.matmul(imaging_representations, torch.transpose(tabular_representations, 0, 1))/self.temperature
        logits_tabular_imaging = torch.matmul(tabular_representations, torch.transpose(imaging_representations, 0, 1))/self.temperature
        loss_imaging_tabular = softcrossentropyloss(mask, logits_imaging_tabular)/torch.sum(mask, 0)
        loss_tabular_imaging = softcrossentropyloss(mask, logits_tabular_imaging)/torch.sum(mask, 0)
        return self.alpha*loss_tabular_imaging.sum() + (1-self.alpha)*loss_imaging_tabular.sum()


if __name__ == '__main__':
    import torch

    batch_dict = {'model.imaging_representations': torch.randn(3, 2),
                  'model.tabular_representations': torch.randn(3, 2),
                  'data.label': torch.empty(3, dtype=torch.long).random_(2)}

    loss = FuseLossMultimodalContrastiveLearning(temperature=0.1,
                                                 imaging_representations='model.imaging_representations',
                                                 tabular_representations='model.tabular_representations',
                                                 label='data.label')
    res = loss(batch_dict)
    print('Loss output = ' + str(res))
