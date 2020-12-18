new_tags = ['sssssssssss', 'ssss', 's', 's']
tags_length = 0
tag_index = 0
while tag_index < len(new_tags) and tags_length + len(new_tags[tag_index]) < 16:
    tags_length += len(new_tags[tag_index])
    tag_index += 1


print(new_tags[:tag_index])
