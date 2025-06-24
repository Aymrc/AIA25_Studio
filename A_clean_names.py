import os

# folder_path = r'C:\Users\broue\Documents\IAAC MaCAD\S3_AIA\Studio\CLIPtest\dataset\Block'
# folder_path = r'C:\Users\broue\Documents\IAAC MaCAD\S3_AIA\Studio\CLIPtest\dataset\Courtyard'
# folder_path = r'C:\Users\broue\Documents\IAAC MaCAD\S3_AIA\Studio\CLIPtest\dataset\C-Shape'
folder_path = r'C:\Users\broue\Documents\IAAC MaCAD\S3_AIA\Studio\CLIPtest\dataset\L-Shape'



for filename in os.listdir(folder_path):
    if filename.endswith('.jpg') and '_Parallel' in filename:
        new_name = filename.replace('_Parallel', '')
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)
        os.rename(old_path, new_path)
        print(f'Renamed: {filename} → {new_name}')
