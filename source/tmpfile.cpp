// source/tmpfile.h

#include "gldcore.h"

#include <map>

static std::map<std::string,std::string> tmpfiles;

// Get a temporary file
void tmpfile_get(
    char *buffer, // buffer into which filename is copied
    size_t len, // length of buffer
    const char *tag // tag to use to refer to filename
    )
{
    if ( tmpfiles.find(std::string(tag)) == tmpfiles.end() )
    {
        const char *ext = "tmp";
        const char *name = tag;

        char label[strlen(tag)+1];
        strcpy(label,tag);
        char *delim = strchr(label,':');
        if ( delim != NULL )
        {
            *delim = '\0';
            ext = label;
            name = delim+1;
        }

        char tmpname[4096];
        const char *tmp = getenv("TMPDIR");
        if ( tmp == NULL )
        {
            tmp = getenv("TMP");
            if ( tmp == NULL )
            {
                tmp = "/tmp";
            }
        }
        snprintf(tmpname,sizeof(tmpname)-1,"%s%sgridlabd_tmp_%s_%u_%s.%s",
            tmp,
            tmp[strlen(tmp)-1] == '/' ? "" : "/",
            global_hostname,
            getpid(),
            name,
            ext);

        int fd = open((const char*)tmpname,O_EXCL|O_CREAT,O_RDWR);
        if ( fd < 0 ) 
        {
            output_warning("unable to create temporary file '%s'",tmpname);
        }
        else
        {
            close(fd);
        }
        
        tmpfiles[std::string(tag)] = std::string(tmpname);
    }
    snprintf(buffer,len-1,"%s",tmpfiles[std::string(tag)].c_str());
}

// Terminate temporary file manager
void tmpfile_term(void)
{
    for ( std::map<std::string,std::string>::iterator item = tmpfiles.begin() ; item != tmpfiles.end() ; item++ )
    {
        unlink(item->second.c_str());
    }
}
