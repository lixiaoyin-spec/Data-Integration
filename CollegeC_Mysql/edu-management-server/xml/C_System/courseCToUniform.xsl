<?xml version="1.0" encoding="GB2312"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" encoding="GB2312" indent="yes"/>

    <xsl:template match="/Courses">
        <classes>
            <xsl:for-each select="course">
                <class>
                    <id><xsl:value-of select="Cno"/></id>
                    <name><xsl:value-of select="Cnm"/></name>
                    <time><xsl:value-of select="Ctm"/></time>
                    <score><xsl:value-of select="Cpt"/></score>
                    <teacher><xsl:value-of select="Tec"/></teacher>
                    <location><xsl:value-of select="Pla"/></location>
                </class>
            </xsl:for-each>
        </classes>
    </xsl:template>
</xsl:stylesheet>