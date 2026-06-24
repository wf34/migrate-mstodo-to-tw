#!/usr/bin/env python3

import os

from tap import Tap

import pypff


class ReaderArgs(Tap):
    input_file: str

    def configure(self):
        self.add_argument('-i', '--input_file')

    def process_args(self):
        if self.input_file == '':
            raise Exception('no input')
        if not os.path.isfile(self.input_file):
            raise Exception('input is not a file ' + self.input_file)


def pst_reader(args: ReaderArgs):
    f = pypff.file()
    opst = pypff.open(args.input_file)
    root = opst.get_root_folder()
    print('>', root.get_name(), root.get_number_of_entries(), root.get_number_of_sub_items(), root.get_number_of_sub_folders(), root.get_number_of_sub_messages(), root.get_number_of_sub_messages(), root.get_number_of_record_sets(), dir(root))
    for folder in root.sub_folders:
        print('-', folder.get_name(), folder.get_number_of_entries(), folder.get_number_of_sub_items(), folder.get_number_of_sub_folders(), folder.get_number_of_sub_messages(), folder.get_number_of_sub_messages(), folder.get_number_of_record_sets())
        for subfolder in folder.sub_folders:
            subfolder_name = subfolder.get_name()
            if subfolder_name != 'Tasks':
                continue

            for ssubfolder in subfolder.sub_folders:
                print('-', ssubfolder.identifier, ssubfolder.get_name(), ssubfolder.get_number_of_entries(), ssubfolder.get_number_of_sub_items(), ssubfolder.get_number_of_sub_folders(), ssubfolder.get_number_of_sub_messages(), ssubfolder.get_number_of_sub_messages(), ssubfolder.get_number_of_record_sets())

                if ssubfolder.get_name() != 'non_tech_reading': #'gentoo': #'A_week':
                    continue
                max_amount_to_check = 100
                amount_to_check = max_amount_to_check
                for m in ssubfolder.sub_messages:
                    print('prints', max_amount_to_check-amount_to_check, 'entry')
                    if 0 == amount_to_check:
                        print('')
                        break
                    if amount_to_check == max_amount_to_check:
                        print(dir(m))
                    print(m.subject, m.html_body, m.get_number_of_entries(), m.get_number_of_record_sets(), m.get_number_of_sub_items(), m.creation_time)
                    for s in m.sub_items:
                        print(s)
                    amount_to_check -= 1

            #for i in subfolder.sub_items:
            #    print('i', i.name)

            #for m in subfolder.sub_messages:
            #    print(m.get_conversation_topic())

            #for r in subfolder.record_sets:
            #    print(dir(r))

        break
        #print(type(folder), dir(folder))


if __name__ == '__main__':
    pst_reader(ReaderArgs().parse_args())
